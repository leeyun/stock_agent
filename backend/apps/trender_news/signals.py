"""관심종목이 추가되면 그 종목 뉴스를 바로 수집한다.

정기 수집(collect_news_task)은 평일 장중에만 돌기 때문에, 주말이나 장 마감 후에 추가한 종목은
다음 수집 때까지 뉴스가 비어 있다. 아직 뉴스가 없는 종목이면 Celery로 그 종목만 수집한다.
"""
import logging
import threading

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.trender_watchlist.models import WatchlistItem

from .models import StockNews
from .tasks import collect_news_for_stock_task

logger = logging.getLogger("apps.trender_news")


@receiver(post_save, sender=WatchlistItem, dispatch_uid="collect_news_on_watchlist_add")
def collect_news_on_watchlist_add(sender, instance, created, **kwargs):
    if not created or StockNews.objects.filter(stock_id=instance.stock_id).exists():
        return
    stock_name = instance.stock.name
    # 관심종목 저장이 커밋된 뒤에 예약한다 (롤백되면 수집하지 않음)
    transaction.on_commit(lambda: _in_background(_enqueue, stock_name))


def _in_background(func, *args):
    # Redis가 꺼져 있으면 연결 실패까지 수 초가 걸리므로 API 응답을 붙잡지 않도록 별도 스레드에서 예약한다
    threading.Thread(target=func, args=args, daemon=True).start()


def _enqueue(stock_name):
    try:
        collect_news_for_stock_task.apply_async(args=[stock_name], retry=False)
    except Exception as exc:
        logger.warning("관심종목 뉴스 수집 예약 실패 (Redis/Celery 확인 필요): %s, %s", stock_name, exc)
    else:
        logger.info("관심종목 추가로 뉴스 수집 예약: %s", stock_name)
