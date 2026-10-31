from rest_framework import serializers

from .models import Stock, StockQuote


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = (
            "id", "code", "ticker", "name", "name_en",
            "market", "sector", "industry", "logo_url",
        )


class StockQuoteSerializer(serializers.ModelSerializer):
    stock_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockQuote
        fields = (
            "stock_id", "current_price", "previous_close", "change_amount", "change_rate",
            "open_price", "day_high", "day_low", "volume", "market_cap",
            "year_high", "year_low", "trading_date", "updated_at",
        )
