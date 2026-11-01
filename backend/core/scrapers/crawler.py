"""네이버 뉴스 검색 API + 네이버 뉴스 본문 크롤러.

검색(`collect_candidates`)과 본문 추출(`fetch_article_content`)을 분리해 두어서
LangGraph 파이프라인(core/graph/news_pipeline.py)이 기사별로 병렬 실행할 수 있다.
환경변수: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_FETCH_CONCURRENCY(기본 2)
"""
import logging
import os
import random
import re
import threading
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("core.scrapers")

NAVER_NEWS_API_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}
MIN_CONTENT_LENGTH = 50
PAGE_SIZE = 100

# 병렬 수집 중에도 네이버 본문 요청은 동시에 이 개수까지만 보낸다 (차단 방지)
_fetch_slots = threading.BoundedSemaphore(int(os.getenv("NAVER_FETCH_CONCURRENCY", "2")))


def search_news(query, display=PAGE_SIZE, start=1):
    """NAVER API HUB 뉴스 검색. 실패하면 빈 리스트."""
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.error("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")
        return []

    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
    }
    params = {"query": query, "display": display, "start": start, "sort": "date"}

    try:
        res = requests.get(NAVER_NEWS_API_URL, headers=headers, params=params, timeout=10)
    except requests.RequestException as exc:
        logger.warning("네이버 뉴스 검색 요청 실패: query=%s, %s", query, exc)
        return []

    if res.status_code != 200:
        logger.warning("네이버 뉴스 검색 실패 (HTTP %s): %s", res.status_code, res.text[:200])
        return []
    return res.json().get('items', [])


def collect_candidates(keyword, target_count=10, target_domains=None, media_name=""):
    """키워드(+언론사명)로 검색해 네이버 뉴스 URL 후보를 최신순으로 모은다. 본문은 가져오지 않는다."""
    candidates = []
    seen_urls = set()
    max_pages = 10 if (target_domains or media_name) else 5

    # API 검색에 들어갈 쿼리 (예: 삼성전자 "한국경제")
    search_query = f'{keyword} "{media_name}"' if media_name else keyword

    for page in range(max_pages):
        items = search_news(search_query, display=PAGE_SIZE, start=1 + page * PAGE_SIZE)
        if not items:
            break

        for item in items:
            naver_url = item.get('link', '')
            original_url = item.get('originallink', '')

            if 'n.news.naver.com' not in naver_url:
                continue
            if target_domains and not any(domain in original_url for domain in target_domains):
                continue

            clean_url = naver_url.split('?')[0]
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)

            candidates.append({
                'keyword': keyword,
                'media': media_name,
                'title': BeautifulSoup(item.get('title', ''), 'html.parser').get_text(),
                'url': naver_url,
                'originallink': original_url,
                'pubDate': item.get('pubDate', ''),
            })
            if len(candidates) >= target_count:
                return candidates

        time.sleep(1)

    return candidates


def fetch_article_content(naver_url):
    """네이버 뉴스 본문 추출 및 정제. 실패하거나 너무 짧으면 빈 문자열."""
    with _fetch_slots:
        time.sleep(random.uniform(0.6, 1.2))
        try:
            res = requests.get(naver_url, headers=HEADERS, timeout=10)
        except requests.RequestException as exc:
            logger.warning("기사 본문 요청 실패: %s, %s", naver_url, exc)
            return ""

    if res.status_code != 200:
        return ""

    soup = BeautifulSoup(res.text, 'html.parser')
    for tag in soup(["script", "style", "iframe", "header", "footer", "aside"]):
        tag.decompose()
    for tag in soup.select(".byline, .copyright, .img_desc, .vod_area"):
        tag.decompose()

    body = (
        soup.select_one("#dic_area") or
        soup.select_one("#newsct_article") or
        soup.select_one("#articleBody")
    )
    if not body:
        return ""

    text = body.get_text(separator='\n')
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()
    return text if len(text) >= MIN_CONTENT_LENGTH else ""


def run_crawler_for_keyword(keyword, target_count=10, target_domains=None, media_name=""):
    """검색 + 본문 추출을 순차로 수행한다 (스크립트/수동 확인용). 본문 추출 실패 기사는 제외."""
    articles = []
    for candidate in collect_candidates(keyword, target_count, target_domains, media_name):
        content = fetch_article_content(candidate['url'])
        if content:
            articles.append({**candidate, 'content': content})
    return articles
