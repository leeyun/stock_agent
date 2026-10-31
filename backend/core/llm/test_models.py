import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. .env 파일에서 환경 변수 불러오기
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    print("에러: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    exit(1)

# 2. API 키 설정
genai.configure(api_key=GOOGLE_API_KEY)

# 3. 모델 목록 조회 및 출력
print("=== 사용 가능한 텍스트 생성 모델 목록 ===")
for m in genai.list_models():
    # 텍스트 생성(generateContent)을 지원하는 모델만 필터링
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
print("========================================")