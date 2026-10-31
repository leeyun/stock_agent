# AI(뉴스 수집 · 학습 · 서빙) 실행 방법

`backend/core/scrapers/`, `backend/core/llm/` 기준. 종목 마스터 수집(`sync_krx_stocks`)은 [backend.md](backend.md)에 있고, 여기는 **뉴스 요약/감성분석 모델**을 만드는 파이프라인이다.

## 전체 흐름

```
1. crawler.py        네이버 뉴스 원문 수집
2. teacher_model.py  Gemini로 요약/감성 라벨링 (teacher)
3. json2jsonl.py     파인튜닝용 instruction 데이터셋(jsonl)으로 변환
4. (이 저장소 밖)     위 데이터셋으로 sLLM 파인튜닝 → Ollama에 "stock-llm"으로 배포
5. ollama_client.py  배포된 모델 호출 + 응답 파싱 (서빙 연동 테스트)
```

지금 상태: 1~3단계 코드는 있고 실행 가능. 4단계(실제 파인튜닝)는 이 코드베이스 밖에서 진행되는 작업이라 여기엔 없다. 5단계는 4단계가 끝나서 Ollama에 `stock-llm` 모델이 실제로 올라가 있어야 의미 있게 동작한다.

## 0. 환경변수

`backend/.env`에 아래 값이 필요하다.

```
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
GEMINI_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434   # 또는 원격 Ollama 서버 주소
```

패키지는 `pip install -r requirements.txt`에 다 포함되어 있다 (`google-genai`, `google-generativeai`, `beautifulsoup4`, `requests` 등).

## 1. 뉴스 원문 수집

```bash
cd backend
python core/scrapers/crawler.py
```

- `crawler.py` 상단의 `TARGET_MEDIA_NAME`, `TARGET_DOMAINS`로 수집할 언론사를 지정한다 (빈 값이면 전체).
- `__main__`의 `keywords` 리스트를 수집하고 싶은 종목명으로 바꾼다.
- 결과는 `backend/core/llm/data/training_data/news_result_{시각}_{키워드}.json`에 저장된다.

## 2. Gemini로 요약/감성 라벨링 (teacher model)

```bash
cd backend/core/llm
python teacher_model.py
```

- `__main__`의 `input_file` 경로를 1단계에서 실제로 생성된 파일명으로 바꿔야 한다 (지금은 예시 파일명이 하드코딩되어 있음).
- 결과는 `data/trained_data/news_result_{시각}_{키워드}.json`에 저장되며, 각 기사에 `llm_analysis: {summary, sentiment, reason, sentiment_code}`가 추가된다.
- `sentiment`는 한글(`호재`/`악재`/`중립`), `sentiment_code`는 백엔드 `Sentiment` enum과 동일한 값(`POSITIVE`/`NEGATIVE`/`NEUTRAL`) — 실서비스 DB에 저장할 땐 `sentiment_code`를 쓰면 된다.
- Gemini API 무료 등급 분당 요청 제한 때문에 기사당 약 4.2초씩 대기한다. 기사 수가 많으면 오래 걸린다.

## 3. 파인튜닝용 데이터셋 변환

```bash
cd backend/core/llm
python json2jsonl.py
```

- `data/trained_data/*.json`을 전부 읽어서 `data/combined_dataset.jsonl`로 합친다.
- 각 줄은 `{"instruction", "input", "output"}` 형태 (표준 instruction-tuning 포맷).

## 4. 파인튜닝 (이 저장소 밖)

`combined_dataset.jsonl`을 가지고 sLLM을 파인튜닝하고, 결과 모델을 Ollama에 `stock-llm`이라는 이름으로 등록한다. 이 단계는 이 코드베이스에 포함되어 있지 않다.

## 5. 서빙 연동 확인

```bash
cd backend/core/llm
python ollama_client.py
```

`OLLAMA_BASE_URL`에 떠 있는 `stock-llm` 모델을 호출해서 결과를 정규식으로 파싱한 뒤 요약/감성/이유를 출력한다. 4단계가 끝나지 않았다면 이 스크립트는 API 에러를 낸다.

## 참고 문서

- 뉴스 요약 AI를 별도 서비스(API)로 분리해서 붙이는 경우의 요청/응답 스펙: [docs/news-summary-ai-contract.md](../docs/news-summary-ai-contract.md)
  - 다만 현재 `ollama_client.py`는 Ollama에 직접 붙어 정규식으로 파싱하는 방식이라, 이 문서의 구조화 JSON 방식과는 다르다. 최종적으로 어느 쪽으로 갈지는 아직 정해지지 않았다.
