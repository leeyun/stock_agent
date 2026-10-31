import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.trender_news.ingest import save_analyzed_article

logger = logging.getLogger("apps.trender_news")

# teacher_model.py가 생성한, Gemini 분석까지 끝난 결과가 쌓이는 위치
TRAINED_DATA_DIR = settings.BASE_DIR / "core" / "llm" / "data" / "trained_data"


class Command(BaseCommand):
    help = "teacher_model.py가 만든 data/trained_data/*.json(Gemini 분석 완료본)을 News/StockNews에 저장한다."

    def handle(self, *args, **options):
        files = sorted(TRAINED_DATA_DIR.glob("*.json"))
        if not files:
            raise CommandError(f"{TRAINED_DATA_DIR}에 분석된 파일이 없습니다. teacher_model.py를 먼저 실행하세요.")

        stock_cache = {}
        created = updated = skipped = 0

        with transaction.atomic():
            for file_path in files:
                with open(file_path, encoding="utf-8") as f:
                    items = json.load(f)

                for item in items:
                    result = save_analyzed_article(item, stock_cache=stock_cache)
                    if result is None:
                        skipped += 1
                        continue
                    _, news_created = result
                    created += int(news_created)
                    updated += int(not news_created)

        message = f"뉴스 저장 완료: 생성 {created}, 갱신 {updated}, 건너뜀 {skipped}"
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(message))
