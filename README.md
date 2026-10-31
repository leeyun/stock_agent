# Trender

종목별 뉴스를 수집·분석해 호재/악재를 판단해주는 주식 뉴스 요약 서비스입니다. 관심종목을 등록하면 실시간에 가까운 시세와 함께, AI가 분석한 관련 뉴스의 감성(호재/악재/중립)과 요약을 확인할 수 있습니다.

## 주요 기능

- **회원 인증**: 이메일 또는 아이디로 로그인, JWT 기반 인증/갱신
- **종목 검색 · 시세**: KRX 전 종목 검색, 시세 조회 (KRX 데이터 자동 동기화)
- **관심종목 관리**: 그룹 생성/이름변경/삭제/순서변경, 종목 추가/이동/삭제
- **뉴스 감성 분석**: 관심종목 관련 뉴스를 수집해 AI로 호재/악재/중립 판단, 3줄 요약, 판단 이유 제공

## Contributors

| [<img src="https://github.com/juan-hong.png" width="100" height="100">](https://github.com/juan-hong) | [<img src="https://github.com/leeyun.png" width="100" height="100">](https://github.com/leeyun) | [<img src="https://github.com/des3738.png" width="100" height="100">](https://github.com/des3738) | [<img src="https://github.com/sooming58.png" width="100" height="100">](https://github.com/sooming58) |
|:---:|:---:|:---:|:---:|
| [juan-hong](https://github.com/juan-hong) | [leeyun](https://github.com/leeyun)<br>LeeYun | [des3738](https://github.com/des3738)<br>표수현 (Suhyeon Pyo) | [sooming58](https://github.com/sooming58) |

## 실행 방법

- [Backend 실행 방법](README/backend.md)
- [Frontend 실행 방법](README/frontend.md)
- [AI(뉴스 수집·학습·서빙) 실행 방법](README/ai.md)

---

# Backend

Django REST Framework 기반 API 서버. `backend/apps/`에 도메인별 앱을 두고, `backend/core/`에 앱에 종속되지 않는 공용 로직(수집기, LLM 연동)을 둡니다.

| 앱 | 역할 |
|---|---|
| `trender_auth` | 회원가입 / 로그인(username·email 겸용) / 내 정보, JWT 발급 |
| `trender_stock` | 종목 검색, 시세 조회, KRX 종목·시세 동기화 커맨드 |
| `trender_watchlist` | 관심종목 그룹/아이템 CRUD, 순서변경, 그룹 간 이동 |
| `trender_news` | 뉴스 조회 API, 뉴스 수집·분석 파이프라인 |

| 구분 | 기술 |
|---|---|
| 언어 / 프레임워크 | Python 3.10, Django 5.2, Django REST Framework |
| 인증 | djangorestframework-simplejwt (JWT access/refresh) |
| API 문서 | drf-spectacular (OpenAPI / Swagger UI) |
| 비동기 · 스케줄링 | Celery + Redis (Celery beat로 시세·뉴스 수집 자동화) |
| DB | SQLite (개발) |
| 시세 · 종목 데이터 | FinanceDataReader |
| 뉴스 크롤링 | BeautifulSoup4, requests, 네이버 뉴스 검색 API |

# Frontend

Flutter 앱. `lib/view`(화면), `lib/view_model`(Provider 기반 상태관리), `lib/service`(API 통신), `lib/model`(데이터 모델)로 구성됩니다.

| 구분 | 기술 |
|---|---|
| 프레임워크 | Flutter (Dart) |
| 상태관리 | provider |
| 네트워킹 | http |
| 보안 저장소 | flutter_secure_storage (JWT 토큰 저장) |
| 기타 | image_picker(프로필 사진), url_launcher(원문 링크 이동) |

# AI

뉴스 수집부터 감성 분석 모델 서빙까지의 파이프라인입니다.

```
크롤링(core/scrapers) → Gemini 라벨링(core/llm, 학습데이터 생성)
                       → 파인튜닝(저장소 외부) → Ollama로 stock-llm 서빙
```

| 구분 | 기술 |
|---|---|
| 뉴스 수집 | BeautifulSoup4, requests, 네이버 뉴스 검색 API |
| 학습 데이터 라벨링 | Google Gemini (`google-genai`) — 요약 / 감성 / 판단 이유 생성 |
| 파인튜닝 서빙 | Ollama — 자체 파인튜닝한 `stock-llm`(Qwen2.5 7B 기반) |
| 자동화 | Celery beat로 관심종목 뉴스 수집 스케줄링 |

# DB Schema
