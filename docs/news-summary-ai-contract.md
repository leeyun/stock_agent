# 뉴스 요약·감성분류 AI API 계약

트렌더 백엔드(뉴스 수집기)가 뉴스 요약·종목 감성분류를 담당하는 AI 서비스에 보내는 요청/응답 형식을 정의한다.
백엔드 모델 기준: `News.summary`, `StockNews.relevance`, `StockNews.sentiment`.

## 요청

```json
{
  "request_id": "news-8231",
  "news": {
    "title": "삼성전자, 3나노 파운드리 수율 개선",
    "content": "원문 본문 텍스트...",
    "press": "연합뉴스",
    "published_at": "2026-09-18T09:00:00+09:00"
  },
  "candidate_stocks": [
    {"stock_id": 1, "code": "005930", "name": "삼성전자"},
    {"stock_id": 2, "code": "000660", "name": "SK하이닉스"}
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `request_id` | string | 요청 상관관계 추적용 id. 응답에 그대로 echo. 백엔드가 발급 (예: `news-{News.id}`) |
| `news.title` | string | 기사 제목 |
| `news.content` | string | 원문 본문 전체 (요약 대상) |
| `news.press` | string | 언론사 |
| `news.published_at` | string (ISO 8601) | 기사 발행 시각 |
| `candidate_stocks` | array | 관련 가능성이 있는 후보 종목 (키워드/티커 매칭으로 사전에 좁혀서 전달) |
| `candidate_stocks[].stock_id` | int | `Stock.id` |
| `candidate_stocks[].code` | string | 종목 코드 |
| `candidate_stocks[].name` | string | 종목명 |

## 응답 (성공, 2xx)

```json
{
  "request_id": "news-8231",
  "summary": "삼성전자가 3나노 파운드리 공정 수율을 개선해 고객사 확대가 기대된다는 내용.",
  "stocks": [
    {"stock_id": 1, "relevance": 0.94, "sentiment": "POSITIVE"},
    {"stock_id": 2, "relevance": 0.12, "sentiment": null}
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `request_id` | string | 요청의 `request_id`를 그대로 echo (필수) |
| `summary` | string | 기사 요약 → `News.summary`에 저장 |
| `stocks[].stock_id` | int | `candidate_stocks`에 있던 `stock_id` 중 하나여야 함 |
| `stocks[].relevance` | float (0.0~1.0) | 기사-종목 관련도 → `StockNews.relevance` |
| `stocks[].sentiment` | string \| null | **아래 4개 값 외 절대 허용 안 함**: `"POSITIVE"`, `"NEGATIVE"`, `"NEUTRAL"`, `null`(무관하거나 판단 보류) → `StockNews.sentiment`. 소문자, 한글, 그 외 문자열 금지 |

`classified_at`은 응답에 포함하지 않는다 — 백엔드가 저장 시점에 직접 채운다 (AI가 준 시각을 신뢰할 이유가 없음).

## 응답 (실패)

HTTP 상태코드로 성공/실패를 구분한다 (2xx = 성공, 4xx/5xx = 실패). 실패 시 바디:

```json
{
  "request_id": "news-8231",
  "error": "에러 메시지"
}
```

## 아직 정해지지 않은 것

- **단건 vs 배치**: 지금 스펙은 뉴스 1건당 요청 1번. 수집기가 하루에 대량으로 뉴스를 처리한다면 비효율적일 수 있어, AI 쪽이 여러 기사를 한 번에 처리할 수 있는지 확인 후 배치 형태(`items: [...]`)로 바꿀지 결정 필요.
- 실제 엔드포인트 URL, 인증 방식 (API 키 / 내부망 여부 등).
