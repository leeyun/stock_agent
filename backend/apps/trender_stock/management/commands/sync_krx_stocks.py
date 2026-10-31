import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.trender_stock.models import Stock
from core.scrapers.krx import fetch_krx_stocks

logger = logging.getLogger("apps.trender_stock")

_TRACKED_FIELDS = ("ticker", "name", "market", "sector", "industry")
_BATCH_SIZE = 500


class Command(BaseCommand):
    help = "KRX 종목 마스터(Stock)를 FinanceDataReader 기준으로 동기화한다."

    def handle(self, *args, **options):
        try:
            krx_stocks = fetch_krx_stocks()
        except Exception as exc:
            raise CommandError(f"KRX 종목 목록 조회 실패: {exc}") from exc

        if not krx_stocks:
            raise CommandError("KRX 종목 목록이 비어 있습니다.")

        codes = [s.code for s in krx_stocks]
        existing = {s.code: s for s in Stock.objects.filter(code__in=codes)}
        now = timezone.now()

        to_create = []
        to_update = []

        for s in krx_stocks:
            obj = existing.get(s.code)
            if obj is None:
                to_create.append(Stock(
                    code=s.code, ticker=s.ticker, name=s.name,
                    market=s.market, sector=s.sector, industry=s.industry,
                    is_active=True,
                ))
                continue

            changed = not obj.is_active
            obj.is_active = True
            for field, value in zip(_TRACKED_FIELDS, (s.ticker, s.name, s.market, s.sector, s.industry)):
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    changed = True
            if changed:
                obj.updated_at = now
                to_update.append(obj)

        with transaction.atomic():
            Stock.objects.bulk_create(to_create, batch_size=_BATCH_SIZE)
            Stock.objects.bulk_update(
                to_update, [*_TRACKED_FIELDS, "is_active", "updated_at"], batch_size=_BATCH_SIZE,
            )
            deactivated = (
                Stock.objects.filter(is_active=True)
                .exclude(code__in=codes)
                .update(is_active=False)
            )

        message = (
            f"KRX 종목 동기화 완료: 생성 {len(to_create)}, 갱신 {len(to_update)}, "
            f"변경없음 {len(krx_stocks) - len(to_create) - len(to_update)}, 상장폐지 처리 {deactivated}"
        )
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(message))
