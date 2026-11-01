# Trender API 명세

Trender 백엔드 REST API의 엔드포인트와 요청, 응답 형식을 정의합니다. 이 문서는 `backend/apps/*/urls.py`, `views.py`, `serializers.py`의 현재 구현을 기준으로 합니다. 실행 중인 서버에서는 Swagger UI(`/api/docs/`)와 OpenAPI 스키마(`/api/schema/`)로도 확인할 수 있습니다.

## 목차

- [공통 사항](#공통-사항)
- [인증](#인증)
- [종목](#종목)
- [관심종목](#관심종목)
- [뉴스](#뉴스)
- [기타](#기타)

## 공통 사항

| 항목 | 값 |
|---|---|
| Base URL | `http://<host>:8000` |
| 인증 방식 | JWT Bearer. `Authorization: Bearer <access>` |
| 기본 권한 | 인증 필요. 예외는 엔드포인트 표에 표시 |
| Access 토큰 수명 | 1시간 |
| Refresh 토큰 수명 | 7일. 갱신할 때마다 새 refresh 토큰을 발급하고 이전 토큰은 블랙리스트에 등록 |
| Content-Type | `application/json` |

### 페이지네이션

페이지네이션을 사용하는 API는 `page`가 0부터 시작합니다 (`ZeroIndexedPageNumberPagination`).

| 쿼리 | 기본값 | 설명 |
|---|---|---|
| `page` | `0` | 페이지 번호 |
| `size` | `20` | 페이지 크기. 최대 100 |

```json
{
  "count": 42,
  "next": "http://.../?page=2&size=20",
  "previous": null,
  "results": []
}
```

`next`와 `previous` URL의 `page` 값은 DRF 내부 값으로 1부터 시작합니다. 클라이언트는 이 URL을 그대로 사용하지 말고 `page`를 직접 계산해야 합니다.

### 오류 응답

| 상태 | 형식 |
|---|---|
| `400` | `{"detail": "..."}` 또는 필드별 `{"field": ["메시지"]}` |
| `401` | `{"detail": "...", "code": "token_not_valid"}` 등 simplejwt 형식 |
| `403` | `{"detail": "..."}` |
| `404` | `{"detail": "No ... matches the given query."}` |
| `503` | `{"detail": "..."}`. 서버 설정이 없어 기능을 사용할 수 없음 |

## 인증

경로 접두사: `/api/auth/`

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| `POST` | `/signup/` | 불필요 | 회원가입과 토큰 발급 |
| `POST` | `/login/` | 불필요 | 아이디 또는 이메일로 로그인 |
| `GET` | `/google/` | 불필요 | Google 로그인용 클라이언트 ID 조회 |
| `POST` | `/google/` | 불필요 | Google ID 토큰으로 로그인. 계정이 없으면 생성 |
| `POST` | `/logout/` | 필요 | refresh 토큰 폐기 |
| `GET` | `/me/` | 필요 | 내 정보 조회 |
| `PUT`, `PATCH` | `/me/` | 필요 | 내 정보 수정 |
| `POST` | `/refresh/` | 불필요 | access 토큰 재발급 |
| `POST` | `/verify/` | 불필요 | 토큰 유효성 확인 |

### POST /api/auth/signup/

요청

```json
{
  "username": "tester",
  "email": "tester@example.com",
  "password": "Trender!2026",
  "password2": "Trender!2026"
}
```

응답 `201`

```json
{
  "user": {"id": 1, "username": "tester", "email": "tester@example.com", "created_at": "2026-09-18T09:00:00+09:00"},
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

- `password`는 Django 비밀번호 검증기를 통과해야 합니다. `password2`가 다르면 `400`을 반환합니다.
- 가입하면 기본 관심 그룹 `나의 관심종목`(`is_default: true`)이 자동으로 생성됩니다.

### POST /api/auth/login/

`username` 필드에 아이디 또는 이메일을 넣습니다. 이메일은 대소문자를 구분하지 않습니다.

```json
{"username": "tester@example.com", "password": "Trender!2026"}
```

응답 `200`은 회원가입과 같은 `{user, access, refresh}` 형식입니다. 자격 증명이 틀리면 `401`을 반환합니다.

### GET /api/auth/google/

```json
{"client_id": "1234567890-abc.apps.googleusercontent.com"}
```

서버 환경변수 `GOOGLE_CLIENT_ID`의 값입니다. 빈 문자열이면 Google 로그인이 비활성 상태입니다.

### POST /api/auth/google/

요청

```json
{"id_token": "<Google Identity Services가 발급한 ID 토큰>"}
```

응답 `200` 또는 `201`

```json
{
  "user": {"id": 3, "username": "gildong", "email": "gildong@gmail.com", "created_at": "..."},
  "access": "<jwt>",
  "refresh": "<jwt>",
  "created": true
}
```

- 서버는 ID 토큰의 서명, 만료, 발급자, 대상(`aud`가 `GOOGLE_CLIENT_ID`와 일치)과 `email_verified`를 검증합니다.
- 같은 이메일의 계정이 있으면 그 계정으로 로그인하고 `200`을 반환합니다.
- 계정이 없으면 비밀번호 없는 계정과 기본 관심 그룹을 만들고 `201`을 반환합니다. 아이디는 이메일 앞부분을 사용하며, 중복되면 숫자를 붙입니다.

| 상태 | 조건 |
|---|---|
| `400` | `id_token` 누락 |
| `401` | 토큰 검증 실패, 이메일 미인증 계정, Google 인증 서버 연결 실패 |
| `403` | 비활성화된 계정 |
| `503` | 서버에 `GOOGLE_CLIENT_ID`가 설정되지 않음 |

### POST /api/auth/logout/

요청 `{"refresh": "<jwt>"}`, 응답 `205` (본문 없음).

`refresh`가 없거나 유효하지 않으면 `400`을 반환합니다. 이미 발급된 access 토큰은 만료될 때까지 유효하므로 클라이언트에서 삭제해야 합니다.

### GET, PUT, PATCH /api/auth/me/

```json
{"id": 1, "username": "tester", "email": "tester@example.com", "created_at": "..."}
```

수정 가능한 필드는 `username`, `email`입니다. `id`, `created_at`은 읽기 전용입니다.

### POST /api/auth/refresh/

요청 `{"refresh": "<jwt>"}`, 응답 `200` `{"access": "<jwt>", "refresh": "<새 jwt>"}`.

### POST /api/auth/verify/

요청 `{"token": "<jwt>"}`. 유효하면 `200 {}`, 아니면 `401`을 반환합니다.

## 종목

경로 접두사: `/api/stock/`

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/?query=` | 종목 검색. 최대 20건, 페이지네이션 없음 |
| `GET` | `/prices/?ids=` | 여러 종목의 시세 일괄 조회. 최대 100개 |

### GET /api/stock/?query={검색어}

활성 종목(`is_active: true`) 중에서 `name` 부분 일치, `code`와 `ticker` 앞부분 일치로 검색합니다. `query`가 비어 있으면 `[]`를 반환합니다.

```json
[
  {
    "id": 1, "code": "005930", "ticker": "005930.KS", "name": "삼성전자", "name_en": "Samsung Electronics",
    "market": "KOSPI", "sector": "...", "industry": "...", "logo_url": ""
  }
]
```

`market`은 `KOSPI`, `KOSDAQ`, `KONEX` 중 하나입니다.

### GET /api/stock/prices/?ids=1,2,3

```json
[
  {
    "stock_id": 1,
    "current_price": "71200.00", "previous_close": "70500.00",
    "change_amount": "700.00", "change_rate": "0.99",
    "open_price": "70800.00", "day_high": "71500.00", "day_low": "70600.00",
    "volume": 12345678, "market_cap": 425000000000000,
    "year_high": "88000.00", "year_low": "49900.00",
    "trading_date": "2026-09-18", "updated_at": "2026-09-18T15:30:00+09:00"
  }
]
```

- Decimal 필드는 문자열로 직렬화됩니다.
- 시세 데이터가 없는 종목은 결과에서 제외됩니다.
- `ids`에 정수가 아닌 값이 있거나 100개를 넘으면 `400`을 반환합니다.

## 관심종목

경로 접두사: `/api/watchlist/`

모든 API는 로그인한 사용자의 그룹만 다룹니다. 다른 사용자의 그룹에 접근하면 `404`를 반환합니다.

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/groups/` | 그룹 목록. 페이지네이션 없음 |
| `POST` | `/groups/` | 그룹 생성 |
| `PATCH` | `/groups/order/` | 그룹 순서 변경 |
| `PATCH` | `/groups/{group_id}/` | 그룹 이름 변경 |
| `DELETE` | `/groups/{group_id}/` | 그룹 삭제. 기본 그룹은 삭제 불가 |
| `GET` | `/groups/{group_id}/items/` | 그룹의 종목 목록. 페이지네이션 사용 |
| `POST` | `/groups/{group_id}/items/` | 종목 추가 |
| `PATCH` | `/groups/{group_id}/items/order/` | 종목 순서 변경 |
| `POST` | `/groups/{group_id}/items/move/` | 다른 그룹으로 종목 이동 |
| `DELETE` | `/groups/{group_id}/items/{stock_id}/` | 종목 제거 |

| 제약 | 값 |
|---|---|
| 사용자당 그룹 수 | 최대 10 |
| 그룹당 종목 수 | 최대 50 |
| 그룹 이름 | 최대 30자. 같은 사용자 안에서 중복 불가 |
| 기본 그룹 | 사용자당 1개. 삭제 불가 |

### GET /groups/

```json
[{"id": 1, "name": "나의 관심종목", "is_default": true, "order": 0}]
```

### POST /groups/

요청 `{"name": "반도체"}`, 응답 `201` `{"id": 2, "name": "반도체", "is_default": false, "order": 1}`.

이름이 중복되거나 그룹 수가 한도를 넘으면 `400`을 반환합니다.

### PATCH /groups/order/

요청 `{"order": [2, 1, 3]}`. 그룹 ID를 원하는 순서대로 나열합니다. 응답 `200`은 순서가 바뀐 그룹 목록입니다. 사용자의 그룹이 아닌 ID가 포함되면 `400`을 반환합니다.

### PATCH /groups/{group_id}/

요청 `{"name": "새 이름"}`, 응답 `200` 그룹 객체.

### DELETE /groups/{group_id}/

응답 `204`. 기본 그룹이면 `400 {"detail": "기본 그룹은 삭제할 수 없습니다."}`를 반환합니다.

### GET /groups/{group_id}/items/?page=0&size=50

```json
{
  "count": 1, "next": null, "previous": null,
  "results": [
    {"id": 10, "stock": {"id": 1, "code": "005930", "name": "삼성전자"}, "order": 0, "added_at": "..."}
  ]
}
```

`stock`은 종목 검색 응답과 같은 형식의 종목 객체입니다.

### POST /groups/{group_id}/items/

요청 `{"stock_id": 1}`, 응답 `201` 아이템 객체.

존재하지 않는 종목, 그룹에 이미 있는 종목, 그룹의 종목 수 한도 초과이면 `400`을 반환합니다.

### PATCH /groups/{group_id}/items/order/

요청 `{"order": [3, 1, 2]}`. 아이템 ID가 아니라 `stock_id` 목록입니다. 응답 `200`은 순서가 바뀐 아이템 목록입니다.

### POST /groups/{group_id}/items/move/

요청 `{"stock_id": 1, "target_group_id": 2}`, 응답 `200` 이동된 아이템.

출발 그룹과 도착 그룹이 같거나, 도착 그룹에 이미 같은 종목이 있거나, 도착 그룹이 가득 찼으면 `400`을 반환합니다.

### DELETE /groups/{group_id}/items/{stock_id}/

응답 `204`.

## 뉴스

경로 접두사: `/api/news/`

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/?stock_id=&page=&size=` | 종목별 분석 뉴스 목록. 발행일 내림차순 |

`stock_id`를 생략하면 전체 종목의 뉴스를 반환합니다. 페이지네이션을 사용합니다.

```json
{
  "count": 12, "next": null, "previous": null,
  "results": [
    {
      "id": 31,
      "stock_id": 1, "stock_name": "삼성전자", "stock_code": "005930",
      "title": "삼성전자, 3나노 파운드리 수율 개선",
      "summary": "문장1\n문장2\n문장3",
      "url": "https://n.news.naver.com/...",
      "origin_url": "https://www.hankyung.com/...",
      "press": "한국경제",
      "published_at": "2026-09-18T09:00:00+09:00",
      "sentiment": "POSITIVE",
      "sentiment_tag": "호재",
      "bullet_summaries": ["문장1", "문장2", "문장3"],
      "ai_reason": "삼성전자 관련 시장 동향 및 기사 핵심 분석 결과 [호재] 요인으로 분류되었습니다."
    }
  ]
}
```

| 필드 | 설명 |
|---|---|
| `sentiment` | `POSITIVE`, `NEGATIVE`, `NEUTRAL` 또는 `null`(분류 전) |
| `sentiment_tag` | `sentiment`의 한글 라벨. `null`이면 `중립` |
| `bullet_summaries` | `summary`를 줄 단위로 나눈 목록. 비어 있으면 `[title]` |
| `ai_reason` | 현재는 고정 문장을 반환합니다. Gemini가 작성한 판단 근거(`StockNews.reason`)를 반환하도록 변경할 예정입니다 |

## 기타

| 경로 | 설명 |
|---|---|
| `/api/schema/` | OpenAPI 3 스키마 |
| `/api/docs/` | Swagger UI |
| `/admin/` | Django 관리자 페이지 |

챗봇 에이전트용 API는 아직 구현되지 않았습니다. 설계안은 [LLM 파이프라인 설계](llm-pipeline.md#향후-계획-챗봇-에이전트)를 참고하세요.
