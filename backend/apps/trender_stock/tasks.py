import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger("apps.trender_stock")


@shared_task
def sync_krx_stocks_task():
    logger.info("Celery beat: sync_krx_stocks 시작")
    call_command("sync_krx_stocks")


@shared_task
def sync_krx_quotes_task():
    logger.info("Celery beat: sync_krx_quotes 시작")
    call_command("sync_krx_quotes")
