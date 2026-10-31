from rest_framework import serializers

from .models import News, StockNews, Sentiment

class NewsDetailSerializer(serializers.ModelSerializer):
    stock_id = serializers.IntegerField(source="stock.id")
    stock_name = serializers.CharField(source="stock.name")
    stock_code = serializers.CharField(source="stock.code")
    title = serializers.CharField(source="news.title")
    summary = serializers.CharField(source="news.summary")
    url = serializers.CharField(source="news.url")
    origin_url = serializers.CharField(source="news.origin_url")
    press = serializers.CharField(source="news.press")
    published_at = serializers.DateTimeField(source="news.published_at")
    sentiment_tag = serializers.SerializerMethodField()
    bullet_summaries = serializers.SerializerMethodField()
    ai_reason = serializers.SerializerMethodField()

    class Meta:
        model = StockNews
        fields = (
            "id", "stock_id", "stock_name", "stock_code", "title",
            "summary", "url", "origin_url", "press", "published_at",
            "sentiment", "sentiment_tag", "bullet_summaries", "ai_reason"
        )

    def get_sentiment_tag(self, obj):
        mapping = {"POSITIVE": "호재", "NEGATIVE": "악재", "NEUTRAL": "중립"}
        return mapping.get(obj.sentiment, "중립")

    def get_bullet_summaries(self, obj):
        summary_text = obj.news.summary or ""
        lines = [line.strip("- •* \t") for line in summary_text.split("\n") if line.strip()]
        return lines if lines else [obj.news.title]

    def get_ai_reason(self, obj):
        tag = self.get_sentiment_tag(obj)
        return f"{obj.stock.name} 관련 시장 동향 및 기사 핵심 분석 결과 [{tag}] 요인으로 분류되었습니다."
