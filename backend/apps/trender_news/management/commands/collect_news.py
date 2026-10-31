import logging

from django.core.management.base import BaseCommand

from apps.trender_news.ingest import save_analyzed_article
from apps.trender_watchlist.models import WatchlistItem
from core.llm import teacher_model
from core.scrapers import crawler

logger = logging.getLogger("apps.trender_news")

ARTICLES_PER_KEYWORD = 10


class Command(BaseCommand):
    help = (
        "관심종목으로 등록된 종목들의 뉴스를 크롤링하고 Gemini(teacher_model)로 분석해 "
        "그 자리에서 News/StockNews에 저장한다."
    )

    def handle(self, *args, **options):
        keywords = list(
            WatchlistItem.objects.order_by().values_list("stock__name", flat=True).distinct()
        )
        if not keywords:
            self.stdout.write(self.style.WARNING("관심종목으로 등록된 종목이 없어 수집할 게 없습니다."))
            return

        stock_cache = {}
        created = updated = 0
        skipped_no_stock = skipped_no_analysis = failed_crawl = 0

        for keyword in keywords:
            self.stdout.write(f"'{keyword}' 뉴스 수집 중...")
            try:
                articles = crawler.run_crawler_for_keyword(keyword, target_count=ARTICLES_PER_KEYWORD)
            except Exception as exc:
                logger.warning("크롤링 실패: keyword=%s, %s", keyword, exc)
                failed_crawl += 1
                continue

            for item in articles:
                analysis = teacher_model.generate_training_data_with_retry(item["content"])
                if analysis is None:
                    skipped_no_analysis += 1
                    continue
                item["llm_analysis"] = analysis

                result = save_analyzed_article(item, stock_cache=stock_cache)
                if result is None:
                    skipped_no_stock += 1
                    continue
                _, news_created = result
                created += int(news_created)
                updated += int(not news_created)

        message = (
            f"뉴스 수집 완료: 생성 {created}, 갱신 {updated}, "
            f"종목 매칭 실패 {skipped_no_stock}, 분석 실패 {skipped_no_analysis}, 크롤링 실패 {failed_crawl}"
        )
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(message))
