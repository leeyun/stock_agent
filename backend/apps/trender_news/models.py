from django.db import models
from core.models import TimeStampModel


class Sentiment(models.TextChoices):
    POSITIVE = "POSITIVE", "호재"
    NEGATIVE = "NEGATIVE", "악재"
    NEUTRAL  = "NEUTRAL",  "중립"


class News(TimeStampModel):
    """기사 본체. 유저·그룹과 무관한 공용 데이터."""
    title        = models.CharField(max_length=300)
    summary      = models.TextField(blank=True)
    url          = models.URLField(max_length=500, unique=True)  # 중복 수집 차단
    origin_url   = models.URLField(max_length=500, blank=True)   # 네이버 originallink
    press        = models.CharField(max_length=50, blank=True)
    published_at = models.DateTimeField(db_index=True)
    # created_at(TimeStampModel) = 수집 시각

    stocks = models.ManyToManyField("trender_stock.Stock", through="StockNews",
                                    related_name="news")

    class Meta:
        db_table = "news"
        ordering = ["-published_at"]
        indexes = [models.Index(fields=["-published_at"])]   # 모아보기 탭


class StockNews(TimeStampModel):
    """종목 ↔ 기사 연결. 호재/악재"""
    stock     = models.ForeignKey("trender_stock.Stock", on_delete=models.CASCADE)
    news      = models.ForeignKey(News, on_delete=models.CASCADE)
    sentiment = models.CharField(max_length=10, choices=Sentiment.choices,
                                 null=True, blank=True, db_index=True)  # null=분류 전
    relevance = models.FloatField(null=True)     # 검색 오염 필터링용 (선택)
    reason = models.TextField(blank=True)        # AI가 해당 감성으로 판단한 이유
    classified_at = models.DateTimeField(null=True)  # 감성 분류가 실제로 수행된 시각

    class Meta:
        db_table = "stock_news"
        constraints = [
            models.UniqueConstraint(fields=["stock", "news"], name="uniq_stock_news"),
        ]
        indexes = [
            models.Index(fields=["stock", "-id"]),   # 종목별 기사 조회
        ]