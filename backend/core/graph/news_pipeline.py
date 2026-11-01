"""관심종목 뉴스 수집·분석 LangGraph 파이프라인.

    START → load_keywords ─(Send: 키워드별)→ search_news → dedupe ─(Send: 기사별)→ process_article → save → END

process_article은 기사 1건을 처리하는 서브그래프다.

    fetch_article → analyze(Gemini) → validate ─┬─ 통과 → END (analyzed에 추가)
                                                ├─ 실패, 재시도 남음 → analyze
                                                └─ 실패 확정 → END (errors에 추가)

- 키워드별 검색과 기사별 처리는 같은 superstep에서 병렬로 실행된다 (동시 실행 수는 max_concurrency).
- Gemini 호출 속도는 news_analyzer의 rate limiter가, 네이버 본문 요청은 crawler의 세마포어가 제한한다.
- DB 저장은 병렬 브랜치에서 하지 않고 save 노드 한 곳에서만 한다 (SQLite 쓰기 잠금 회피).
"""
import logging
import operator
from typing import Annotated, TypedDict

from django.conf import settings
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from apps.trender_news.ingest import save_analyzed_article
from apps.trender_news.models import StockNews
from apps.trender_stock.models import Stock
from apps.trender_watchlist.models import WatchlistItem
from core.llm import news_analyzer
from core.scrapers import crawler

logger = logging.getLogger("core.graph")

DEFAULT_ARTICLES_PER_KEYWORD = 10
MAX_ANALYZE_ATTEMPTS = 2


class PipelineState(TypedDict, total=False):
    keywords: list[str] | None
    articles_per_keyword: int
    candidates: Annotated[list[dict], operator.add]  # search_news 브랜치들이 누적
    pending: list[dict]                               # dedupe 후 분석할 기사
    analyzed: Annotated[list[dict], operator.add]     # process_article 브랜치들이 누적
    errors: Annotated[list[dict], operator.add]
    stats: dict


class ArticleState(TypedDict, total=False):
    article: dict
    content: str
    analysis: dict | None
    attempts: int
    last_error: str
    analyzed: Annotated[list[dict], operator.add]
    errors: Annotated[list[dict], operator.add]


class ArticleOutput(TypedDict):
    analyzed: Annotated[list[dict], operator.add]
    errors: Annotated[list[dict], operator.add]


def _error(stage, article_or_keyword, message):
    if isinstance(article_or_keyword, dict):
        return {"stage": stage, "keyword": article_or_keyword.get("keyword"),
                "url": article_or_keyword.get("url"), "error": message}
    return {"stage": stage, "keyword": article_or_keyword, "url": None, "error": message}


# ---------------------------------------------------------------------------
# 기사 1건 서브그래프
# ---------------------------------------------------------------------------
def fetch_article(state: ArticleState):
    article = state["article"]
    content = crawler.fetch_article_content(article["url"])
    if not content:
        return {"content": "", "errors": [_error("fetch", article, "본문 추출 실패 또는 본문이 너무 짧음")]}
    return {"content": content, "attempts": 0}


def route_after_fetch(state: ArticleState):
    return "analyze" if state.get("content") else END


def analyze(state: ArticleState):
    article = state["article"]
    attempts = state.get("attempts", 0) + 1
    try:
        result = news_analyzer.analyze_article(article["keyword"], article["title"], state["content"])
    except Exception as exc:  # API 오류, 파싱 실패 모두 validate에서 재시도 여부를 판단
        logger.warning("Gemini 분석 실패 (%s회): %s, %s", attempts, article["url"], exc)
        return {"analysis": None, "attempts": attempts, "last_error": f"{type(exc).__name__}: {exc}"}
    return {"analysis": result.model_dump(), "attempts": attempts, "last_error": ""}


def validate(state: ArticleState):
    analysis = state.get("analysis")
    problem = state.get("last_error") if analysis is None else \
        news_analyzer.validation_error(news_analyzer.NewsAnalysis(**analysis))

    if problem is None:
        return {"analyzed": [{"article": state["article"], "analysis": analysis}]}
    if state["attempts"] < MAX_ANALYZE_ATTEMPTS:
        return {"last_error": problem}
    return {"errors": [_error("analyze", state["article"], problem)]}


def route_after_validate(state: ArticleState):
    if state.get("analysis") is not None and not state.get("last_error"):
        return END
    return "analyze" if state["attempts"] < MAX_ANALYZE_ATTEMPTS else END


def _build_article_graph():
    graph = StateGraph(ArticleState, output_schema=ArticleOutput)
    graph.add_node("fetch_article", fetch_article)
    graph.add_node("analyze", analyze)
    graph.add_node("validate", validate)
    graph.add_edge(START, "fetch_article")
    graph.add_conditional_edges("fetch_article", route_after_fetch, ["analyze", END])
    graph.add_edge("analyze", "validate")
    graph.add_conditional_edges("validate", route_after_validate, ["analyze", END])
    return graph.compile()


# ---------------------------------------------------------------------------
# 상위 그래프
# ---------------------------------------------------------------------------
def load_keywords(state: PipelineState):
    keywords = state.get("keywords")
    if keywords is None:
        keywords = list(
            WatchlistItem.objects.order_by().values_list("stock__name", flat=True).distinct()
        )
    return {"keywords": keywords}


def route_keywords(state: PipelineState):
    per_keyword = state.get("articles_per_keyword") or DEFAULT_ARTICLES_PER_KEYWORD
    sends = [Send("search_news", {"keyword": k, "articles_per_keyword": per_keyword})
             for k in state["keywords"]]
    return sends or END


def search_news(payload: dict):
    keyword = payload["keyword"]
    try:
        candidates = crawler.collect_candidates(keyword, target_count=payload["articles_per_keyword"])
    except Exception as exc:
        logger.warning("뉴스 검색 실패: keyword=%s, %s", keyword, exc)
        return {"errors": [_error("search", keyword, f"{type(exc).__name__}: {exc}")]}
    if not candidates:
        return {"errors": [_error("search", keyword, "검색 결과 없음")]}
    return {"candidates": candidates}


def dedupe(state: PipelineState):
    """종목 마스터에 없는 키워드와, 이미 같은 종목으로 저장된 기사를 Gemini 호출 전에 걸러낸다."""
    candidates = state.get("candidates", [])
    keywords = {c["keyword"] for c in candidates}
    known_stocks = set(Stock.objects.filter(name__in=keywords).values_list("name", flat=True))
    already_saved = set(
        StockNews.objects.filter(
            stock__name__in=keywords, news__url__in=[c["url"] for c in candidates],
        ).values_list("stock__name", "news__url")
    )

    pending, seen, errors = [], set(), []
    for c in candidates:
        key = (c["keyword"], c["url"])
        if key in seen or key in already_saved:
            continue
        seen.add(key)
        if c["keyword"] not in known_stocks:
            errors.append(_error("dedupe", c, "종목 마스터에서 종목을 찾을 수 없음"))
            continue
        pending.append(c)

    logger.info("뉴스 후보 %s건 중 신규 %s건 (이미 저장 %s건)",
                len(candidates), len(pending), len(candidates) - len(pending) - len(errors))
    return {"pending": pending, "errors": errors}


def route_articles(state: PipelineState):
    sends = [Send("process_article", {"article": a}) for a in state.get("pending", [])]
    return sends or "save"


def save(state: PipelineState):
    stock_cache = {}
    created = updated = skipped = 0
    for item in state.get("analyzed", []):
        article, analysis = item["article"], item["analysis"]
        result = save_analyzed_article(
            {**article, "llm_analysis": {
                "summary": analysis["summary"],
                "sentiment_code": analysis["sentiment"],
                "reason": analysis["reason"],
                "relevance": analysis["relevance"],
            }},
            stock_cache=stock_cache,
        )
        if result is None:
            skipped += 1
            continue
        _, news_created = result
        created += int(news_created)
        updated += int(not news_created)

    stats = {
        "keywords": len(state.get("keywords") or []),
        "candidates": len(state.get("candidates", [])),
        "analyzed": len(state.get("analyzed", [])),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": len(state.get("errors", [])),
    }
    return {"stats": stats}


def build_news_pipeline():
    graph = StateGraph(PipelineState)
    graph.add_node("load_keywords", load_keywords)
    graph.add_node("search_news", search_news)
    graph.add_node("dedupe", dedupe)
    graph.add_node("process_article", _build_article_graph())
    graph.add_node("save", save)

    graph.add_edge(START, "load_keywords")
    graph.add_conditional_edges("load_keywords", route_keywords, ["search_news", END])
    graph.add_edge("search_news", "dedupe")
    graph.add_conditional_edges("dedupe", route_articles, ["process_article", "save"])
    graph.add_edge("process_article", "save")
    graph.add_edge("save", END)
    return graph.compile()


def run_news_pipeline(keywords=None, articles_per_keyword=DEFAULT_ARTICLES_PER_KEYWORD, max_concurrency=None):
    """파이프라인을 실행하고 최종 state를 반환한다. keywords=None이면 관심종목 전체."""
    pipeline = build_news_pipeline()
    concurrency = max_concurrency or settings.NEWS_PIPELINE_CONCURRENCY
    return pipeline.invoke(
        {"keywords": keywords, "articles_per_keyword": articles_per_keyword},
        config={"max_concurrency": concurrency},
    )
