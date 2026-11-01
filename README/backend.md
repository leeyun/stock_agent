# Backend 가이드

Django REST Framework 기반 API 서버입니다. 이 문서의 명령은 별도 표기가 없으면 `backend/` 디렉터리 기준입니다.

## 목차

- [구성](#구성)
- [설치](#설치)
- [환경변수](#환경변수)
- [실행](#실행)
- [데이터 동기화와 스케줄](#데이터-동기화와-스케줄)
- [외부 공개 (ngrok)](#외부-공개-ngrok)
- [관리 명령](#관리-명령)
- [테스트](#테스트)
- [문제 해결](#문제-해결)

## 구성

| 경로 | 설명 |
|---|---|
| `config/` | settings, URL 라우팅, Celery 앱 |
| `apps/trender_auth/` | 회원가입, 로그인(아이디 또는 이메일), Google 로그인, 내 정보 |
| `apps/trender_stock/` | KRX 종목 마스터와 시세, 종목 검색 API |
| `apps/trender_watchlist/` | 관심 그룹과 관심종목 API. 가입 시 기본 그룹 자동 생성 |
| `apps/trender_news/` | 뉴스와 종목-뉴스 감성 데이터, 뉴스 피드 API, 수집 명령 |
| `core/graph/` | LangGraph 뉴스 파이프라인 |
| `core/llm/` | Gemini 뉴스 분석기, 분석 성능 평가 스크립트 |
| `core/scrapers/` | 네이버 뉴스 검색과 본문 추출, KRX 데이터 수집 |

API 엔드포인트는 [API 명세](../docs/api-spec.md)와 실행 중인 서버의 Swagger 문서(`/api/docs/`)에서 확인할 수 있습니다.

## 설치

저장소 루트에서 `scripts\setup.bat`을 실행하면 아래 과정을 한 번에 처리합니다. 수동으로 설치하는 방법은 다음과 같습니다.

```bat
cd backend
C:\development\python\python-3.12.10\python.exe -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
```

`.env`를 직접 만든 경우 `DJANGO_SECRET_KEY`를 새로 생성해 넣습니다.

```bat
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

관리자 페이지를 쓰려면 관리자 계정을 만듭니다.

```bat
python manage.py createsuperuser
```

## 환경변수

`backend/.env`에 설정합니다. `.env`는 Git에 포함되지 않으며, 형식은 `.env.example`을 따릅니다.

### 필수

| 변수 | 설명 |
|---|---|
| `DJANGO_SECRET_KEY` | JWT와 세션 서명 키. 값이 바뀌면 기존 로그인 토큰이 모두 무효화됩니다 |

### 기능별

비어 있어도 서버는 실행되며, 해당 기능만 동작하지 않습니다.

| 변수 | 기능 | 발급처 |
|---|---|---|
| `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | 뉴스 검색 | NAVER API HUB |
| `GEMINI_API_KEY` | 뉴스 분석 | Google AI Studio |
| `GOOGLE_CLIENT_ID` | Google 로그인 | Google Cloud Console, OAuth 클라이언트 ID (웹 애플리케이션) |

### 선택

주석을 해제하고 값을 바꿀 때만 적용됩니다. 빈 값(`KEY=`)으로 두면 기본값 대신 빈 값이 들어가므로 주의합니다.

| 변수 | 기본값 | 설명 |
|---|---|---|
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | 뉴스 분석 모델 |
| `GEMINI_RPM` | `15` | Gemini 분당 요청 한도. 사용하는 요금제에 맞춥니다 |
| `NEWS_PIPELINE_CONCURRENCY` | `4` | 뉴스 파이프라인에서 동시에 실행할 브랜치 수 |
| `NAVER_FETCH_CONCURRENCY` | `2` | 네이버 기사 본문 동시 요청 수 |
| `CORS_ALLOWED_ORIGINS` | 없음 | 웹 배포 주소 (쉼표로 구분). `DEBUG`일 때는 `localhost`의 모든 포트를 자동 허용합니다 |

## 실행

```bat
scripts\backend.bat
```

미적용 마이그레이션이 있으면 먼저 적용한 뒤 `127.0.0.1:8000`에서 서버를 실행합니다. 직접 실행하는 경우는 다음과 같습니다.

```bat
python manage.py runserver 127.0.0.1:8000
```

| 주소 | 설명 |
|---|---|
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/schema/ | OpenAPI 스키마 |
| http://localhost:8000/admin/ | 관리자 페이지 |

VS Code에서는 실행 구성 `Backend (Django)` 또는 `Backend + Web (Chrome)`으로 디버깅할 수 있습니다.

## 데이터 동기화와 스케줄

### 수동 실행

| 명령 | 스크립트 | 설명 |
|---|---|---|
| `python manage.py sync_krx_stocks` | `scripts\sync_krx.bat` | KRX 종목 마스터 동기화. 상장폐지 종목 처리 포함 |
| `python manage.py sync_krx_quotes` | `scripts\sync_krx.bat` | 종목 시세 동기화 |
| `python manage.py collect_news` | `scripts\collect_news.bat` | 관심종목 뉴스 수집과 분석 |

### 자동 실행 (Celery)

Celery beat가 아래 일정으로 작업을 예약합니다. 시간대는 `Asia/Seoul`입니다.

| 작업 | 일정 |
|---|---|
| `sync_krx_stocks_task` | 매일 08:30 |
| `sync_krx_quotes_task` | 평일 09:00-15:55, 5분 간격 |
| `collect_news_task` | 평일 09:00-16:00, 매시 정각 |
| `collect_news_for_stock_task` | 관심종목을 추가할 때. 그 종목의 뉴스가 하나도 없으면 최신 기사 3건을 바로 수집 (`apps/trender_news/signals.py`) |

Celery는 Redis가 필요합니다. `scripts\dev.bat celery`는 Docker Compose로 Redis를 띄운 뒤 worker와 beat를 실행합니다. 개별 실행은 다음과 같습니다.

```bat
docker compose up -d redis
scripts\celery.bat worker
scripts\celery.bat beat
```

## 외부 공개 (ngrok)

`scripts\manager.bat`은 외부에서 접속할 수 있도록 전체 서비스를 실행하는 메뉴형 도구입니다.

| 메뉴 | 동작 |
|---|---|
| 1. 전체 실행 | Docker Desktop 시작과 엔진 대기(최대 120초), Redis 컨테이너, ngrok 터널, 웹 빌드 확인, Django, Celery worker와 beat를 순서대로 실행하고 외부 주소를 출력 |
| 2. ngrok 공개 주소 확인 | ngrok 로컬 API(`127.0.0.1:4040`)에서 현재 주소를 읽어 출력 |
| 3. 웹 빌드 | 외부 공개용 웹을 다시 빌드. 프론트엔드 코드를 바꾼 뒤 실행 |
| 4. 키 설정 상태 확인 | `.env` 키가 채워졌는지 출력. 비밀 값은 길이만 표시 |
| 5. DB 마이그레이션 | `makemigrations` 후 `migrate` |
| 6. 서비스 모두 종료 | 제목이 `Trender`로 시작하는 창(ngrok, Django, Celery)을 닫고 Redis 컨테이너 중지 |
| 7. 새 Django 앱 생성 | `apps/<이름>`에 앱 생성 |

### 구성

- ngrok은 포트 8000 하나만 공개합니다. Django가 `frontend/build/web`의 웹 빌드를 함께 서빙하므로(`config/frontend.py`) 같은 주소에서 웹과 API를 모두 사용할 수 있습니다.
- 외부 공개용 웹은 `API_BASE_URL`을 비워서 빌드합니다. 이 경우 웹은 자신이 열린 주소의 API를 호출합니다.
- 개발용 `scripts\web.bat`(포트 3000)은 이 빌드와 별개이며 그대로 사용할 수 있습니다.

### 설정

| 변수 | 설명 |
|---|---|
| `NGROK_AUTHTOKEN` | 비워두면 `ngrok.yml`에 등록된 토큰을 사용합니다 |
| `NGROK_DOMAIN` | 사용할 도메인. 비워두면 계정에 자동 배정된 dev 도메인을 사용합니다. 유료 플랜의 다른 도메인을 쓸 때만 입력합니다 |

ngrok 토큰은 https://dashboard.ngrok.com/get-started/your-authtoken 에서 확인하고 `ngrok config add-authtoken <토큰>`으로 등록합니다. 무료 플랜도 계정마다 dev 도메인(`xxxx.ngrok-free.dev`) 하나가 자동 배정되고, 다시 실행해도 같은 주소를 씁니다. 주소는 ngrok 대시보드의 Gateway > Domains에서 확인할 수 있습니다. Google 로그인을 외부 주소에서 쓰려면 이 주소를 Google OAuth의 승인된 JavaScript 원본에 한 번 추가합니다.

무료 플랜에서는 처음 접속할 때 ngrok 경고 페이지가 한 번 표시되며, 방문자가 확인을 눌러야 앱으로 넘어갑니다.

ngrok 주소로 접속하면 서버가 이 PC에서 그대로 인터넷에 공개됩니다. 현재 설정은 `DEBUG=True`이므로 오류 화면에 내부 정보가 노출될 수 있습니다. 시연이나 테스트 용도로만 사용합니다.

## 관리 명령

### collect_news

```bat
python manage.py collect_news [--keywords 종목명 ...] [--per-keyword N] [--concurrency N]
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--keywords` | 관심종목 전체 | 지정한 종목명만 수집. 종목 마스터에 있는 이름이어야 합니다 |
| `--per-keyword` | `10` | 키워드당 검색할 최신 기사 수 |
| `--concurrency` | `NEWS_PIPELINE_CONCURRENCY` | 동시 실행 브랜치 수 |

이미 같은 종목으로 저장된 기사는 다시 분석하지 않습니다. 파이프라인 구조는 [뉴스 분석 파이프라인](ai.md)을 참고하세요.

### import_trained_news

```bat
python manage.py import_trained_news
```

`core/llm/data/trained_data/*.json`의 분석 결과를 `News`와 `StockNews`에 저장합니다. 같은 파일을 다시 실행해도 중복 저장되지 않습니다.

## 테스트

```bat
python manage.py test
```

저장소 루트의 `scripts\test.bat`은 백엔드 테스트와 프론트엔드 정적 분석을 함께 실행합니다. 뉴스 파이프라인 테스트는 네이버와 Gemini 호출을 모의 객체로 대체하므로 API 키 없이 실행됩니다.

## 문제 해결

| 증상 | 원인과 조치 |
|---|---|
| 서버 시작 시 `KeyError: 'DJANGO_SECRET_KEY'` | `.env`가 없거나 키가 비어 있습니다. `scripts\setup.bat`을 실행하거나 키를 생성해 넣습니다 |
| `collect_news`가 "검색 결과 없음"만 출력 | 네이버 키가 비어 있거나 잘못되었습니다 |
| 뉴스 분석 단계에서 `ImproperlyConfigured` | `GEMINI_API_KEY`가 비어 있습니다 |
| 분석 중 429 오류가 반복됨 | `GEMINI_RPM`을 요금제 한도 이하로 낮춥니다 |
| Celery worker가 연결 오류로 종료 | Redis가 실행 중인지 확인합니다 (`docker compose up -d redis`) |
| `.env` 값을 바꿨는데 반영되지 않음 | `.env`는 서버 시작 시에만 읽습니다. 서버를 다시 시작합니다 |
