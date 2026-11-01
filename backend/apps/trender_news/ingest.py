"""크롤링+Gemini 분석이 끝난 기사 dict를 News/StockNews에 저장하는 공용 로직.

`import_trained_news`(파일에서 읽어 저장)와 뉴스 파이프라인(core/graph/news_pipeline.py의 save 노드)
둘 다 이 함수를 통해 같은 방식으로 저장한다.
"""
import logging
from email.utils import parsedate_to_datetime

from django.utils import timezone

from apps.trender_stock.models import Stock

from .models import News, StockNews

logger = logging.getLogger("apps.trender_news")


def parse_pub_date(pub_date_str):
    """네이버 API의 RFC 822 pubDate를 파싱한다. 실패하면 현재 시각으로 대체."""
    try:
        dt = parsedate_to_datetime(pub_date_str)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    except (TypeError, ValueError):
        return timezone.now()


def save_analyzed_article(item, stock_cache=None):
    """분석이 끝난 기사 하나를 News/StockNews에 저장한다.

    item: crawler.py가 만든 dict + llm_analysis({summary, sentiment_code, reason, relevance?}) 포함.
    stock_cache: {keyword: Stock|None} 캐시. 여러 건을 반복 처리할 때 넘기면 중복 조회를 줄인다.

    반환값: (news, created) 또는 저장 못 했으면 None.
    """
    analysis = item.get("llm_analysis")
    if not analysis:
        return None

    keyword = item.get("keyword", "")
    if stock_cache is not None and keyword in stock_cache:
        stock = stock_cache[keyword]
    else:
        stock = Stock.objects.filter(name=keyword).first()
        if stock_cache is not None:
            stock_cache[keyword] = stock

    if stock is None:
        logger.warning("종목을 찾을 수 없어 건너뜀: keyword=%s, url=%s", keyword, item.get("url"))
        return None

    summary_lines = analysis.get("summary") or []
    summary_text = "\n".join(summary_lines) if isinstance(summary_lines, list) else str(summary_lines)

    news, news_created = News.objects.update_or_create(
        url=item["url"],
        defaults={
            "title": item.get("title", ""),
            "summary": summary_text,
            "origin_url": item.get("originallink", ""),
            "press": item.get("media", ""),
            "published_at": parse_pub_date(item.get("pubDate", "")),
        },
    )

    StockNews.objects.update_or_create(
        stock=stock, news=news,
        defaults={
            "sentiment": analysis.get("sentiment_code"),
            # 뉴스 파이프라인은 Gemini가 매긴 관련도를 넘긴다. 예전 분석 파일(import_trained_news)에는
            # 관련도가 없으므로 "이 종목 키워드로 검색된 기사"라는 의미로 1.0을 쓴다.
            "relevance": analysis.get("relevance", 1.0),
            "reason": analysis.get("reason", ""),
            "classified_at": timezone.now(),
        },
    )

    return news, news_created
