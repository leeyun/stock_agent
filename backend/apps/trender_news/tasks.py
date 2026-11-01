import logging

from celery import shared_task
from django.core.management import call_command

from .models import StockNews

logger = logging.getLogger("apps.trender_news")

# 관심종목을 추가했을 때 바로 수집할 기사 수 (기사 1건당 Gemini 1회 호출)
NEWS_PER_NEW_WATCHLIST_STOCK = 3


@shared_task
def collect_news_task():
    logger.info("Celery beat: collect_news 시작")
    call_command("collect_news")


@shared_task
def collect_news_for_stock_task(stock_name):
    """관심종목 추가 직후 그 종목 뉴스만 수집한다 (signals.py에서 예약)."""
    if StockNews.objects.filter(stock__name=stock_name).exists():
        logger.info("관심종목 뉴스 수집 건너뜀 (이미 뉴스 있음): %s", stock_name)
        return
    logger.info("관심종목 추가: %s 뉴스 수집 시작", stock_name)
    call_command("collect_news", "--keywords", stock_name, "--per-keyword", str(NEWS_PER_NEW_WATCHLIST_STOCK))
