import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger("apps.trender_news")


@shared_task
def collect_news_task():
    logger.info("Celery beat: collect_news 시작")
    call_command("collect_news")
