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
from core.graph.news_pipeline import run_news_pipeline
from core.llm.news_analyzer import NewsAnalysis

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


class CollectNewsPipelineTests(TestCase):
    """collect_news → core/graph/news_pipeline.py. 네이버·Gemini 호출은 mock."""

    PIPELINE = "core.graph.news_pipeline"

    def setUp(self):
        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)
        self.sk = Stock.objects.create(code="000660", ticker="000660.KS", name="SK하이닉스", market=Market.KOSPI)
        self.user = User.objects.create_user(username="watcher", email="w@example.com", password="pw12345!")
        group = WatchlistGroup.objects.get(user=self.user, is_default=True)
        WatchlistItem.objects.create(group=group, stock=self.samsung, order=0)

    @staticmethod
    def _candidate(keyword, n):
        return {"keyword": keyword, "media": "", "title": f"{keyword} 기사 {n}",
                "url": f"https://n.news.naver.com/{keyword}/{n}", "originallink": "", "pubDate": ""}

    @staticmethod
    def _analysis(**overrides):
        values = {"summary": ["요약1", "요약2", "요약3"], "sentiment": "POSITIVE",
                  "reason": "수주 확대", "relevance": 0.85, **overrides}
        return NewsAnalysis(**values)

    def _run(self, candidates_by_keyword, analyze, content="본문 " * 20, **kwargs):
        with patch(f"{self.PIPELINE}.crawler.collect_candidates",
                   side_effect=lambda kw, target_count: candidates_by_keyword.get(kw, [])) as crawl, \
             patch(f"{self.PIPELINE}.crawler.fetch_article_content", return_value=content) as fetch, \
             patch(f"{self.PIPELINE}.news_analyzer.analyze_article", **analyze) as llm:
            result = run_news_pipeline(**kwargs)
        return result, crawl, fetch, llm

    def test_no_watchlist_items_does_nothing(self):
        WatchlistItem.objects.all().delete()
        with patch(f"{self.PIPELINE}.crawler.collect_candidates") as crawl:
            call_command("collect_news")
        crawl.assert_not_called()
        self.assertEqual(News.objects.count(), 0)

    def test_crawls_analyzes_and_saves_for_watchlisted_stocks(self):
        result, crawl, _, llm = self._run(
            {"삼성전자": [self._candidate("삼성전자", 1)]}, {"return_value": self._analysis()},
        )

        crawl.assert_called_once_with("삼성전자", target_count=10)
        llm.assert_called_once_with("삼성전자", "삼성전자 기사 1", "본문 " * 20)
        news = News.objects.get(url="https://n.news.naver.com/삼성전자/1")
        self.assertEqual(news.summary, "요약1\n요약2\n요약3")
        link = StockNews.objects.get(stock=self.samsung, news=news)
        self.assertEqual(link.sentiment, Sentiment.POSITIVE)
        self.assertEqual(link.reason, "수주 확대")
        self.assertAlmostEqual(link.relevance, 0.85)
        self.assertEqual(result["stats"]["created"], 1)

    def test_already_saved_article_is_not_reanalyzed(self):
        candidate = self._candidate("삼성전자", 1)
        news = News.objects.create(title="기존", url=candidate["url"], published_at=timezone.now())
        StockNews.objects.create(stock=self.samsung, news=news, sentiment=Sentiment.NEUTRAL)

        _, _, fetch, llm = self._run({"삼성전자": [candidate]}, {"return_value": self._analysis()})

        fetch.assert_not_called()
        llm.assert_not_called()

    def test_analysis_error_is_retried_then_recorded_not_fatal(self):
        result, _, _, llm = self._run(
            {"삼성전자": [self._candidate("삼성전자", 1)]}, {"side_effect": RuntimeError("429")},
        )

        self.assertEqual(llm.call_count, 2)
        self.assertEqual(News.objects.count(), 0)
        self.assertEqual([e["stage"] for e in result["errors"]], ["analyze"])

    def test_invalid_analysis_is_retried(self):
        _, _, _, llm = self._run(
            {"삼성전자": [self._candidate("삼성전자", 1)]},
            {"side_effect": [self._analysis(reason=" "), self._analysis()]},
        )

        self.assertEqual(llm.call_count, 2)
        self.assertEqual(StockNews.objects.get(stock=self.samsung).reason, "수주 확대")

    def test_fetch_failure_skips_analysis(self):
        result, _, _, llm = self._run(
            {"삼성전자": [self._candidate("삼성전자", 1)]}, {"return_value": self._analysis()}, content="",
        )

        llm.assert_not_called()
        self.assertEqual([e["stage"] for e in result["errors"]], ["fetch"])

    def test_unknown_stock_keyword_is_not_analyzed(self):
        result, _, _, llm = self._run(
            {"없는종목": [self._candidate("없는종목", 1)]}, {"return_value": self._analysis()},
            keywords=["없는종목"],
        )

        llm.assert_not_called()
        self.assertEqual([e["stage"] for e in result["errors"]], ["dedupe"])

    def test_multiple_keywords_and_articles_run_in_parallel_and_all_save(self):
        candidates = {kw: [self._candidate(kw, n) for n in range(3)] for kw in ("삼성전자", "SK하이닉스")}
        result, crawl, _, llm = self._run(
            candidates, {"return_value": self._analysis()},
            keywords=["삼성전자", "SK하이닉스"], max_concurrency=4,
        )

        self.assertEqual(crawl.call_count, 2)
        self.assertEqual(llm.call_count, 6)
        self.assertEqual(StockNews.objects.filter(stock=self.samsung).count(), 3)
        self.assertEqual(StockNews.objects.filter(stock=self.sk).count(), 3)
        self.assertEqual(result["stats"]["created"], 6)


class CollectNewsOnWatchlistAddTests(APITestCase):
    """관심종목 추가 시 그 종목 뉴스 수집 예약 (signals.py, tasks.collect_news_for_stock_task)."""

    ENQUEUE = "apps.trender_news.signals.collect_news_for_stock_task.apply_async"
    BACKGROUND = "apps.trender_news.signals._in_background"  # 테스트에서는 스레드 없이 바로 실행

    def setUp(self):
        self.samsung = Stock.objects.create(code="005930", ticker="005930.KS", name="삼성전자", market=Market.KOSPI)
        self.user = User.objects.create_user(username="adder", email="a@example.com", password="pw12345!")
        self.client.force_authenticate(self.user)
        self.group = WatchlistGroup.objects.get(user=self.user, is_default=True)

    def _add(self, **patch_kwargs):
        url = reverse("trender_watchlist:item-list", args=[self.group.id])
        with patch(self.ENQUEUE, **patch_kwargs) as enqueue, \
             patch(self.BACKGROUND, side_effect=lambda func, *args: func(*args)), \
             self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(url, {"stock_id": self.samsung.id})
        return res, enqueue

    def test_adding_stock_without_news_schedules_collection(self):
        res, enqueue = self._add()
        self.assertEqual(res.status_code, 201)
        enqueue.assert_called_once_with(args=["삼성전자"], retry=False)

    def test_stock_with_news_is_not_collected_again(self):
        news = News.objects.create(title="기존", url="https://example.com/x", published_at=timezone.now())
        StockNews.objects.create(stock=self.samsung, news=news, sentiment=Sentiment.NEUTRAL)
        _, enqueue = self._add()
        enqueue.assert_not_called()

    def test_broker_down_does_not_break_adding(self):
        res, _ = self._add(side_effect=ConnectionError("redis down"))
        self.assertEqual(res.status_code, 201)
        self.assertTrue(WatchlistItem.objects.filter(group=self.group, stock=self.samsung).exists())

    def test_moving_item_does_not_schedule(self):
        item = WatchlistItem.objects.create(group=self.group, stock=self.samsung, order=0)
        with patch(self.ENQUEUE) as enqueue, self.captureOnCommitCallbacks(execute=True):
            item.order = 1
            item.save()
        enqueue.assert_not_called()

    def test_task_collects_only_that_stock(self):
        from .tasks import collect_news_for_stock_task
        with patch("apps.trender_news.tasks.call_command") as cmd:
            collect_news_for_stock_task("삼성전자")
        cmd.assert_called_once_with("collect_news", "--keywords", "삼성전자", "--per-keyword", "3")

    def test_task_skips_when_news_arrived_meanwhile(self):
        from .tasks import collect_news_for_stock_task
        news = News.objects.create(title="기존", url="https://example.com/y", published_at=timezone.now())
        StockNews.objects.create(stock=self.samsung, news=news, sentiment=Sentiment.NEUTRAL)
        with patch("apps.trender_news.tasks.call_command") as cmd:
            collect_news_for_stock_task("삼성전자")
        cmd.assert_not_called()
