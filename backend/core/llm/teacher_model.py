import json
import os
import sys
import time
import warnings
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Windows 기본 콘솔(cp949)에서 이모지 print 시 UnicodeEncodeError 나는 것 방지
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# SDK 내부 AFC 경고 메시지 숨기기
warnings.filterwarnings("ignore", category=UserWarning)

# 1. 환경 변수 불러오기
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    print("에러: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    exit(1)

# 2. 최신 GenAI 클라이언트 초기화
client = genai.Client(api_key=GOOGLE_API_KEY)

# 3. 가장 안정적인 Flash 모델로 지정
MODEL_NAME = "gemini-3.5-flash-lite"

# 4. JSON 구조화를 위한 Pydantic Schema 정의
class NewsAnalysisSchema(BaseModel):
    summary: list[str] = Field(description="3줄 요약 (문장 3개 리스트)")
    sentiment: str = Field(description="감성 분석: '호재', '악재', '중립' 중 하나")
    reason: str = Field(description="판단 이유 (1~2문장)")

# 백엔드 trender_news.Sentiment enum과 동일한 매핑.
# 실서비스에 붙일 때 이 sentiment_code(POSITIVE/NEGATIVE/NEUTRAL)를 그대로 StockNews.sentiment에 저장하면 된다.
SENTIMENT_LABEL_TO_CODE = {
    "호재": "POSITIVE",
    "악재": "NEGATIVE",
    "중립": "NEUTRAL",
}

def generate_training_data(news_text):
    prompt = f"""
    당신은 금융/주식 전문 분석가입니다. 아래 뉴스 기사를 분석하세요.

    [뉴스 원문]
    {news_text}

    [분석 지침]
    1. summary: 기사의 핵심 내용을 3개의 문장 리스트로 정리하세요.
    2. sentiment: 반드시 '호재', '악재', '중립' 중 하나만 선택하세요.
    3. reason: 해당 감성으로 판단한 이유를 1~2문장으로 설명하세요.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=NewsAnalysisSchema,
        ),
    )
    
    result = json.loads(response.text)
    result["sentiment_code"] = SENTIMENT_LABEL_TO_CODE.get(result.get("sentiment"))
    return result


def generate_training_data_with_retry(news_text, max_retries=3):
    """__main__ 루프에 있던 429/일시 오류 재시도 로직을 그대로 옮긴 버전.
    Celery task처럼 반복 호출하는 곳에서 재시도/레이트리밋 대기를 직접 구현하지 않도록 제공.
    실패하면 None을 반환한다."""
    for attempt in range(1, max_retries + 1):
        try:
            result = generate_training_data(news_text)
            time.sleep(4.2)  # 분당 요청 수 제한 준수
            return result
        except APIError as e:
            wait_time = 45 if e.code == 429 else 5
            print(f"  -> ⚠️ API 에러({e.code})! {wait_time}초 후 재시도 ({attempt}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"  -> ❌ 분석 실패 (알 수 없는 에러): {e}")
            return None
    return None


if __name__ == "__main__":
    input_file = "data/training_data/news_result_260915_1520_신한지주.json" 

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
    except FileNotFoundError:
        print(f"에러: {input_file} 파일을 찾을 수 없습니다.")
        exit(1)

    if not news_data:
        print("분석할 기사 데이터가 없습니다.")
        exit(0)

    keyword = news_data[0].get("keyword", "키워드없음")
    current_time = datetime.now().strftime("%y%m%d_%H%M") 
    
    output_filename = f"news_result_{current_time}_{keyword}.json"
    output_file = os.path.join("data/trained_data", output_filename)

    processed_data = []

    for idx, item in enumerate(news_data, start=1):
        content = item.get("content", "").strip()
        title = item.get("title", "제목 없음")
        
        if not content:
            print(f"[{idx}/{len(news_data)}] 본문 없음 패스: {title}")
            continue

        print(f"[{idx}/{len(news_data)}] Gemini 분석 중: {title[:20]}...")
        
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                llm_result = generate_training_data(content)
                item["llm_analysis"] = llm_result
                processed_data.append(item)
                success = True
                
            except APIError as e:
                retry_count += 1
                if e.code == 429:
                    wait_time = 45
                    print(f"  -> ⚠️ 429 할당량 초과! {wait_time}초 대기 후 재시도 ({retry_count}/{max_retries})")
                else:
                    wait_time = 5
                    print(f"  -> ⚠️ API 에러 발생 ({e.code})! {wait_time}초 후 재시도 ({retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"  -> ❌ 분석 실패 (알 수 없는 에러): {e}")
                break

        # 분당 요청 수 제한을 준수하기 위한 대기 (4.2초)
        if success:
            time.sleep(4.2)

    if processed_data:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n작업 완료! 총 {len(processed_data)}건의 데이터가 '{output_file}'에 저장되었습니다.")
    else:
        print("\n저장할 데이터가 없습니다.")