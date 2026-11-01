import logging

from django.core.management.base import BaseCommand

from core.graph.news_pipeline import DEFAULT_ARTICLES_PER_KEYWORD, run_news_pipeline

logger = logging.getLogger("apps.trender_news")


class Command(BaseCommand):
    help = (
        "관심종목 뉴스를 LangGraph 파이프라인(core/graph/news_pipeline.py)으로 수집하고 "
        "Gemini로 분석해 News/StockNews에 저장한다. 이미 저장된 기사는 다시 분석하지 않는다."
    )

    def add_arguments(self, parser):
        parser.add_argument("--keywords", nargs="+", help="관심종목 대신 이 종목명들만 수집")
        parser.add_argument("--per-keyword", type=int, default=DEFAULT_ARTICLES_PER_KEYWORD,
                            help=f"키워드당 검색할 최신 기사 수 (기본 {DEFAULT_ARTICLES_PER_KEYWORD})")
        parser.add_argument("--concurrency", type=int, help="동시 실행 브랜치 수 (기본 NEWS_PIPELINE_CONCURRENCY)")

    def handle(self, *args, **options):
        result = run_news_pipeline(
            keywords=options["keywords"],
            articles_per_keyword=options["per_keyword"],
            max_concurrency=options["concurrency"],
        )

        if not result.get("keywords"):
            self.stdout.write(self.style.WARNING("관심종목으로 등록된 종목이 없어 수집할 게 없습니다."))
            return

        for error in result.get("errors", []):
            logger.warning("뉴스 파이프라인 [%s] %s %s: %s",
                           error["stage"], error["keyword"], error["url"] or "", error["error"])

        stats = result["stats"]
        message = (
            f"뉴스 수집 완료: 키워드 {stats['keywords']}, 후보 {stats['candidates']}, "
            f"분석 {stats['analyzed']}, 생성 {stats['created']}, 갱신 {stats['updated']}, "
            f"저장 건너뜀 {stats['skipped']}, 오류 {stats['errors']}"
        )
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(message))
