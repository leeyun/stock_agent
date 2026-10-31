import os
import sys
import json
import time
import random
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Windows 기본 콘솔(cp949)에서 이모지 print 시 UnicodeEncodeError 나는 것 방지
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# .env 파일 로드
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

# 🎯 언론사 제어 변수 (다른 언론사 수집 시 이 두 변수만 변경)
TARGET_MEDIA_NAME = "한국경제"       # API 검색어 조합용 언론사명 (빈 문자열 "" 설정 시 전체)
TARGET_DOMAINS = ["hankyung.com"]    # 도메인 사전 검증용 (빈 리스트 [] 설정 시 전체)

def get_naver_api_hub_news(query, display=100, start=1):
    """NAVER API HUB 검색 호출"""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ .env 파일에서 NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET을 찾을 수 없습니다.")
        return []

    url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?query={query}&display={display}&start={start}&sort=date"
    
    headers = {
        "X-NCP-APIGW-API-KEY-ID": CLIENT_ID,
        "X-NCP-APIGW-API-KEY": CLIENT_SECRET
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get('items', [])
        else:
            print(f"  -> ❌ API 호출 실패 (HTTP {res.status_code}): {res.text}")
            return []
    except Exception as e:
        print(f"  -> ❌ API 요청 에러: {e}")
        return []

def extract_naver_article(naver_url):
    """네이버 뉴스 본문 추출 및 정규식 정제"""
    try:
        time.sleep(random.uniform(0.6, 1.2))
        res = requests.get(naver_url, headers=HEADERS, timeout=10)
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
        
        if body:
            text = body.get_text(separator='\n')
            text = text.replace('\xa0', ' ')
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n', text)
            return text.strip()
    except Exception:
        pass
    return ""

def run_crawler_for_keyword(keyword, target_count=50, target_domains=None, media_name=""):
    """키워드 + 언론사명 조합 검색 및 수집 로직"""
    results = []
    seen_urls = set()
    start = 1
    max_api_calls = 10 if (target_domains or media_name) else 5

    # API 검색에 들어갈 쿼리 생성 (예: 삼성전자 "한국경제")
    search_query = f'{keyword} "{media_name}"' if media_name else keyword
    print(f"🔍 '{keyword}' 수집 시작 (API 검색어: '{search_query}', 목표: {target_count}건)...")

    while len(results) < target_count and start <= (max_api_calls * 100):
        # API 호출 시 search_query 전달
        items = get_naver_api_hub_news(search_query, display=100, start=start)
        if not items:
            break

        for item in items:
            if len(results) >= target_count:
                break

            naver_url = item.get('link', '')
            original_url = item.get('originallink', '')

            if 'n.news.naver.com' not in naver_url:
                continue

            # 도메인 2차 검증
            if target_domains:
                if not any(domain in original_url for domain in target_domains):
                    continue

            clean_url = naver_url.split('?')[0]
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)

            title = BeautifulSoup(item.get('title', ''), 'html.parser').get_text()
            content = extract_naver_article(naver_url)

            if len(content) < 50:
                continue

            # 저장 데이터에는 원본 순수 keyword 명시
            results.append({
                'keyword': keyword,
                'media': media_name,
                'title': title,
                'url': naver_url,
                'originallink': original_url,
                'pubDate': item.get('pubDate', ''),
                'content': content
            })
            print(f"  [{len(results)}/{target_count}] 성공: {title[:25]}...")

        start += 100
        time.sleep(1)

    return results

if __name__ == "__main__":
    keywords = [
        "삼성전자", "SK하이닉스",
        "LG에너지솔루션", "POSCO홀딩스",
        "현대차", "HD한국조선해양",
        "삼성바이오로직스", "셀트리온",
        "KB금융", "신한지주",
        "하이브", "CJ제일제당"
    ]

    target_max_count = 50
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "llm", "data", "training_data")
    os.makedirs(save_dir, exist_ok=True)

    total_keywords = len(keywords)
    print(f"🚀 총 {total_keywords}개 키워드 연속 수집 시작 (키워드당 {target_max_count}건)")
    print(f"🎯 설정 언론사: {TARGET_MEDIA_NAME} ({TARGET_DOMAINS})\n")

    for idx, keyword in enumerate(keywords, start=1):
        print(f"\n==================================================")
        print(f"[{idx}/{total_keywords}] 키워드 작업 시작: '{keyword}'")
        print(f"==================================================")

        news_data = run_crawler_for_keyword(
            keyword=keyword,
            target_count=target_max_count,
            target_domains=TARGET_DOMAINS,
            media_name=TARGET_MEDIA_NAME
        )

        if news_data:
            current_time = datetime.now().strftime("%y%m%d_%H%M")
            filename = f"news_result_{current_time}_{keyword}.json"
            file_path = os.path.join(save_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(news_data, f, ensure_ascii=False, indent=4)

            print(f"✅ '{keyword}' {len(news_data)}건 저장 완료 -> {file_path}")
        else:
            print(f"⚠️ '{keyword}' 조건에 맞는 유효 기사를 찾지 못했습니다.")

        time.sleep(2)

    print("\n🎉 모든 키워드의 뉴스 데이터 수집이 성공적으로 종료되었습니다!")