import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.trender_stock.models import Stock, StockQuote
from core.scrapers.krx_quotes import fetch_krx_quotes

logger = logging.getLogger("apps.trender_stock")

_TRACKED_FIELDS = (
    "current_price", "previous_close", "change_amount", "change_rate",
    "open_price", "day_high", "day_low", "volume", "market_cap", "trading_date",
)
_BATCH_SIZE = 500


class Command(BaseCommand):
    help = "KRX 현재 시세(StockQuote)를 FinanceDataReader 기준으로 동기화한다."

    def handle(self, *args, **options):
        try:
            krx_quotes = fetch_krx_quotes()
        except Exception as exc:
            raise CommandError(f"KRX 시세 조회 실패: {exc}") from exc

        if not krx_quotes:
            raise CommandError("KRX 시세 목록이 비어 있습니다.")

        codes = [q.code for q in krx_quotes]
        stock_id_by_code = dict(Stock.objects.filter(code__in=codes).values_list("code", "id"))
        existing = {q.stock_id: q for q in StockQuote.objects.filter(stock_id__in=stock_id_by_code.values())}
        trading_date = timezone.localdate()
        now = timezone.now()

        to_create = []
        to_update = []
        skipped = 0

        for q in krx_quotes:
            stock_id = stock_id_by_code.get(q.code)
            if stock_id is None:
                # Stock 마스터에 없는 종목(sync_krx_stocks 미실행/최신화 지연) — 건너뜀
                skipped += 1
                continue

            values = (
                q.current_price, q.previous_close, q.change_amount, q.change_rate,
                q.open_price, q.day_high, q.day_low, q.volume, q.market_cap, trading_date,
            )

            obj = existing.get(stock_id)
            if obj is None:
                to_create.append(StockQuote(stock_id=stock_id, **dict(zip(_TRACKED_FIELDS, values))))
                continue

            for field, value in zip(_TRACKED_FIELDS, values):
                setattr(obj, field, value)
            obj.updated_at = now
            to_update.append(obj)

        with transaction.atomic():
            StockQuote.objects.bulk_create(to_create, batch_size=_BATCH_SIZE)
            StockQuote.objects.bulk_update(
                to_update, [*_TRACKED_FIELDS, "updated_at"], batch_size=_BATCH_SIZE,
            )

        message = (
            f"KRX 시세 동기화 완료: 생성 {len(to_create)}, 갱신 {len(to_update)}, "
            f"건너뜀(마스터 없음) {skipped}"
        )
        logger.info(message)
        self.stdout.write(self.style.SUCCESS(message))
