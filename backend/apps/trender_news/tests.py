import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.trender_stock.models import Market, Stock
from apps.trender_watchlist.models import WatchlistGroup, WatchlistItem

from .models import News, Sentiment, StockNews

User = get_user_model()


class NewsEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", email="t@example.com", password="pw12345!")
        self.client.force_authenticate(self.user)

        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)
        self.sk = Stock.objects.create(code="000660", ticker="000660.KS", name="SK하이닉스", market=Market.KOSPI)

        now = timezone.now()
        self.news1 = News.objects.create(
            title="삼성전자 파운드리 호재", summary="요약1", url="https://example.com/1",
            press="한국경제", published_at=now,
        )
        self.news2 = News.objects.create(
            title="SK하이닉스 실적 발표", summary="요약2", url="https://example.com/2",
            press="연합뉴스", published_at=now - timezone.timedelta(hours=1),
        )
        StockNews.objects.create(
            stock=self.samsung, news=self.news1,
            sentiment=Sentiment.POSITIVE, relevance=0.9, reason="수율 개선 소식",
        )
        StockNews.objects.create(
            stock=self.sk, news=self.news2,
            sentiment=Sentiment.NEUTRAL, relevance=0.5, reason="실적 컨센서스 부합",
        )

    def test_list_returns_all_news_ordered_by_published_at(self):
        res = self.client.get(reverse("trender_news:news-list"))
        self.assertEqual(res.status_code, 200)
        titles = [n["title"] for n in res.json()["results"]]
        self.assertEqual(titles, [self.news1.title, self.news2.title])

    def test_list_includes_stock_and_sentiment_fields(self):
        res = self.client.get(reverse("trender_news:news-list"))
        first = res.json()["results"][0]
        self.assertEqual(first["stock_code"], "005930")
        self.assertEqual(first["sentiment"], "POSITIVE")
        self.assertEqual(first["sentiment_tag"], "호재")
        self.assertEqual(first["bullet_summaries"], ["요약1"])

    def test_filter_by_stock_id(self):
        res = self.client.get(reverse("trender_news:news-list"), {"stock_id": self.sk.id})
        results = res.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], self.news2.title)

    def test_pagination_params(self):
        res = self.client.get(reverse("trender_news:news-list"), {"page": 0, "size": 1})
        body = res.json()
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["count"], 2)


class ImportTrainedNewsCommandTests(TestCase):
    def setUp(self):
        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)

    def _write_fixture(self, tmp_path, filename, items):
        (tmp_path / filename).write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

    def _run_with_dir(self, tmp_path):
        with patch("apps.trender_news.management.commands.import_trained_news.TRAINED_DATA_DIR", tmp_path):
            call_command("import_trained_news")

    def test_creates_news_and_stocknews(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._write_fixture(tmp_path, "a.json", [{
                "keyword": "삼성전자", "media": "한국경제", "title": "삼성전자 호재 기사",
                "url": "https://example.com/1", "originallink": "https://hankyung.com/1",
                "pubDate": "Mon, 26 Sep 2022 12:00:00 +0900",
                "content": "본문",
                "llm_analysis": {
                    "summary": ["첫줄", "둘째줄", "셋째줄"],
                    "sentiment": "호재", "reason": "수율 개선", "sentiment_code": "POSITIVE",
                },
            }])
            self._run_with_dir(tmp_path)

        news = News.objects.get(url="https://example.com/1")
        self.assertEqual(news.summary, "첫줄\n둘째줄\n셋째줄")
        link = StockNews.objects.get(stock=self.samsung, news=news)
        self.assertEqual(link.sentiment, Sentiment.POSITIVE)
        self.assertEqual(link.reason, "수율 개선")

    def test_skips_item_without_matching_stock(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._write_fixture(tmp_path, "a.json", [{
                "keyword": "존재하지않는종목", "media": "한국경제", "title": "제목",
                "url": "https://example.com/2", "originallink": "", "pubDate": "",
                "content": "본문",
                "llm_analysis": {"summary": ["요약"], "sentiment": "중립", "reason": "", "sentiment_code": "NEUTRAL"},
            }])
            self._run_with_dir(tmp_path)

        self.assertFalse(News.objects.filter(url="https://example.com/2").exists())

    def test_rerun_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            item = {
                "keyword": "삼성전자", "media": "한국경제", "title": "제목",
                "url": "https://example.com/3", "originallink": "", "pubDate": "",
                "content": "본문",
                "llm_analysis": {"summary": ["요약"], "sentiment": "호재", "reason": "이유", "sentiment_code": "POSITIVE"},
            }
            self._write_fixture(tmp_path, "a.json", [item])
            self._run_with_dir(tmp_path)
            self._run_with_dir(tmp_path)

        self.assertEqual(News.objects.filter(url="https://example.com/3").count(), 1)
        self.assertEqual(StockNews.objects.filter(stock=self.samsung).count(), 1)


class CollectNewsCommandTests(TestCase):
    def setUp(self):
        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)
        self.user = User.objects.create_user(username="watcher", email="w@example.com", password="pw12345!")
        group = WatchlistGroup.objects.get(user=self.user, is_default=True)
        WatchlistItem.objects.create(group=group, stock=self.samsung, order=0)

    def test_no_watchlist_items_does_nothing(self):
        WatchlistItem.objects.all().delete()
        call_command("collect_news")
        self.assertEqual(News.objects.count(), 0)

    def test_crawls_analyzes_and_saves_for_watchlisted_stocks(self):
        fake_article = {
            "keyword": "삼성전자", "media": "한국경제", "title": "테스트 기사",
            "url": "https://example.com/collected", "originallink": "https://hankyung.com/1",
            "pubDate": "", "content": "본문",
        }
        fake_analysis = {
            "summary": ["요약1", "요약2", "요약3"],
            "sentiment": "호재", "reason": "테스트 이유", "sentiment_code": "POSITIVE",
        }

        with patch("apps.trender_news.management.commands.collect_news.crawler.run_crawler_for_keyword",
                   return_value=[fake_article]) as mock_crawl, \
             patch("apps.trender_news.management.commands.collect_news.teacher_model."
                   "generate_training_data_with_retry", return_value=fake_analysis) as mock_analyze:
            call_command("collect_news")

        mock_crawl.assert_called_once_with("삼성전자", target_count=10)
        mock_analyze.assert_called_once_with("본문")

        news = News.objects.get(url="https://example.com/collected")
        link = StockNews.objects.get(stock=self.samsung, news=news)
        self.assertEqual(link.sentiment, Sentiment.POSITIVE)

    def test_analysis_failure_is_skipped_not_fatal(self):
        fake_article = {
            "keyword": "삼성전자", "media": "한국경제", "title": "테스트 기사",
            "url": "https://example.com/failed", "originallink": "", "pubDate": "", "content": "본문",
        }
        with patch("apps.trender_news.management.commands.collect_news.crawler.run_crawler_for_keyword",
                   return_value=[fake_article]), \
             patch("apps.trender_news.management.commands.collect_news.teacher_model."
                   "generate_training_data_with_retry", return_value=None):
            call_command("collect_news")

        self.assertFalse(News.objects.filter(url="https://example.com/failed").exists())
