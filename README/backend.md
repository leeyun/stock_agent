# Backend 실행 방법

Django REST Framework 기반 API 서버. `backend/` 디렉토리 기준.

## 1. 가상환경 생성 및 활성화

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

## 2. 패키지 설치

```bash
pip install -r requirements.txt
```

## 3. 환경변수 설정

`.env.example`을 복사해 `.env`를 만들고 값을 채운다.

```bash
copy .env.example .env
```

최소 `DJANGO_SECRET_KEY`는 반드시 채워야 서버가 뜬다. 뉴스/AI 수집기를 쓰려면 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`도 필요 (자세한 내용은 [AI 실행 방법](ai.md) 참고).

## 4. DB 마이그레이션

```bash
python manage.py migrate
```

## 5. (선택) 관리자 계정 생성

```bash
python manage.py createsuperuser
```

## 6. (선택) 종목 마스터 데이터 채우기

검색/시세 API가 의미 있으려면 KRX 종목 데이터가 있어야 한다.

```bash
python manage.py sync_krx_stocks
```

## 7. 서버 실행

```bash
python manage.py runserver 0.0.0.0:8000
```

- API 문서(Swagger): http://127.0.0.1:8000/api/docs/
- 관리자 페이지: http://127.0.0.1:8000/admin/

## Windows 스크립트로 한 번에

`Scripts/win/` 아래 배치 스크립트로 위 과정을 대신할 수 있다.

| 스크립트 | 역할 |
|---|---|
| `Scripts/win/setup.bat` | venv 생성, 패키지 설치, `.env` 생성, migrate, superuser 생성까지 최초 1회 셋업 |
| `Scripts/win/dev.bat` | venv 활성화 후 `runserver` 실행 |
| `Scripts/win/migrate.bat` | makemigrations → migrate |
| `Scripts/win/sync_krx.bat` | KRX 종목 마스터 동기화 |
| `Scripts/win/reset_db.bat` | ⚠️ DB와 마이그레이션 전체 삭제 후 재생성 (되돌릴 수 없음) |

## 테스트

```bash
python manage.py test apps
```
