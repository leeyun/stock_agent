from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.scrapers.krx import KrxStock, fetch_krx_stocks
from core.scrapers.krx_quotes import KrxQuote
from .models import Market, Stock, StockQuote

User = get_user_model()


class StockEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", email="t@example.com", password="pw12345!")
        self.client.force_authenticate(self.user)
        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)
        self.sk = Stock.objects.create(code="000660", ticker="000660.KS", name="SK하이닉스", market=Market.KOSPI)
        StockQuote.objects.create(
            stock=self.samsung, current_price=70000, previous_close=69000,
            change_amount=1000, change_rate=1.45,
        )

    def test_search_by_name(self):
        res = self.client.get(reverse("trender_stock:search"), {"query": "삼성"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([s["code"] for s in res.json()], ["005930"])

    def test_search_blank_query_returns_empty(self):
        res = self.client.get(reverse("trender_stock:search"))
        self.assertEqual(res.json(), [])

    def test_prices_bulk_only_returns_existing_quotes(self):
        ids = f"{self.samsung.id},{self.sk.id}"
        res = self.client.get(reverse("trender_stock:prices"), {"ids": ids})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([q["stock_id"] for q in res.json()], [self.samsung.id])

    def test_prices_rejects_non_integer_ids(self):
        res = self.client.get(reverse("trender_stock:prices"), {"ids": "1,abc"})
        self.assertEqual(res.status_code, 400)


class SyncKrxStocksCommandTests(TestCase):
    def _run_with(self, krx_stocks):
        with patch("apps.trender_stock.management.commands.sync_krx_stocks.fetch_krx_stocks",
                   return_value=krx_stocks):
            call_command("sync_krx_stocks")

    def test_creates_new_stocks(self):
        self._run_with([
            KrxStock(code="005930", ticker="005930.KS", name="삼성전자",
                     market=Market.KOSPI, sector="", industry="반도체"),
        ])
        stock = Stock.objects.get(code="005930")
        self.assertEqual(stock.name, "삼성전자")
        self.assertTrue(stock.is_active)

    def test_rerun_updates_existing_and_deactivates_missing(self):
        self._run_with([
            KrxStock(code="005930", ticker="005930.KS", name="삼성전자",
                     market=Market.KOSPI, sector="", industry="반도체"),
            KrxStock(code="000660", ticker="000660.KS", name="SK하이닉스",
                     market=Market.KOSPI, sector="", industry="반도체"),
        ])
        # 두 번째 수집에는 000660이 빠짐 (상장폐지/이관 시나리오)
        self._run_with([
            KrxStock(code="005930", ticker="005930.KS", name="삼성전자우",
                     market=Market.KOSPI, sector="", industry="반도체"),
        ])

        self.assertEqual(Stock.objects.get(code="005930").name, "삼성전자우")
        self.assertFalse(Stock.objects.get(code="000660").is_active)


class FetchKrxStocksTests(SimpleTestCase):
    def test_degrades_gracefully_when_krx_desc_unavailable(self):
        def fake_listing(market):
            if market == "KRX":
                return pd.DataFrame([{"Code": "005930", "Name": "삼성전자", "Market": "KOSPI"}])
            raise RuntimeError("HTTP Error 404: Not Found")

        with patch("core.scrapers.krx.fdr.StockListing", side_effect=fake_listing):
            stocks = fetch_krx_stocks()

        self.assertEqual(len(stocks), 1)
        self.assertEqual(stocks[0].code, "005930")
        self.assertEqual(stocks[0].sector, "")
        self.assertEqual(stocks[0].industry, "")


class SyncKrxQuotesCommandTests(TestCase):
    def setUp(self):
        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)

    def _run_with(self, krx_quotes):
        with patch("apps.trender_stock.management.commands.sync_krx_quotes.fetch_krx_quotes",
                   return_value=krx_quotes):
            call_command("sync_krx_quotes")

    def test_creates_quote_for_known_stock(self):
        self._run_with([
            KrxQuote(code="005930", current_price=70000, previous_close=69000,
                     change_amount=1000, change_rate=1.45, open_price=69500,
                     day_high=70500, day_low=69000, volume=1000000, market_cap=1000000000000),
        ])
        quote = StockQuote.objects.get(stock=self.samsung)
        self.assertEqual(quote.current_price, 70000)
        self.assertEqual(quote.change_amount, 1000)

    def test_unknown_code_is_skipped_not_errored(self):
        self._run_with([
            KrxQuote(code="999999", current_price=1, previous_close=1,
                     change_amount=0, change_rate=0.0, open_price=1,
                     day_high=1, day_low=1, volume=1, market_cap=1),
        ])
        self.assertEqual(StockQuote.objects.count(), 0)

    def test_rerun_overwrites_existing_quote(self):
        self._run_with([
            KrxQuote(code="005930", current_price=70000, previous_close=69000,
                     change_amount=1000, change_rate=1.45, open_price=69500,
                     day_high=70500, day_low=69000, volume=1000000, market_cap=1000000000000),
        ])
        self._run_with([
            KrxQuote(code="005930", current_price=71000, previous_close=70000,
                     change_amount=1000, change_rate=1.43, open_price=70000,
                     day_high=71500, day_low=69800, volume=1200000, market_cap=1010000000000),
        ])
        quote = StockQuote.objects.get(stock=self.samsung)
        self.assertEqual(quote.current_price, 71000)
        self.assertEqual(StockQuote.objects.count(), 1)
