from django.conf import settings
from django.db import models
from core.models import TimeStampModel


class Market(models.TextChoices):
    """특정 마켓 enum"""
    KOSPI = "KOSPI", "코스피"
    KOSDAQ = "KOSDAQ", "코스닥"
    KONEX = "KONEX", "코넥스"


class Stock(TimeStampModel):
    """종목 마스터, FDR로 1일 1회 동기화."""
    code        = models.CharField(max_length=10, unique=True, db_index=True)
    ticker      = models.CharField(max_length=20, unique=True)
    name        = models.CharField(max_length=100, db_index=True)
    name_en     = models.CharField(max_length=200, blank=True)
    market      = models.CharField(max_length=10, choices=Market.choices)
    sector      = models.CharField(max_length=100, blank=True)
    industry    = models.CharField(max_length=100, blank=True)
    logo_url    = models.URLField(max_length=500, blank=True)
    is_active   = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "stock"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"]),
            models.Index(fields=["is_active", "code"]),
        ]

    def __str__(self):
        return f"[{self.name}] ({self.code})"


class StockQuote(TimeStampModel):
    """현재 시세. 종목당 1행, 수집기가 bulk_update로 덮어씀."""
    stock           = models.OneToOneField(Stock, on_delete=models.CASCADE,
                                       related_name="quote", primary_key=True)
    current_price   = models.DecimalField(max_digits=20, decimal_places=2)
    previous_close  = models.DecimalField(max_digits=20, decimal_places=2)
    change_amount   = models.DecimalField(max_digits=20, decimal_places=2)
    change_rate    = models.DecimalField(max_digits=8,  decimal_places=2)
    open_price     = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    day_high       = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    day_low        = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    volume         = models.BigIntegerField(null=True)
    market_cap     = models.BigIntegerField(null=True)
    year_high      = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    year_low       = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    trading_date   = models.DateField(null=True)          # 시세 기준일
    # updated_at(TimeStampModel) = 프론트 "15:30 기준" 표시용

    class Meta:
        db_table = "stock_quotes"
