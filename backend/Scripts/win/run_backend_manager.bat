@echo off
chcp 65001 > nul
title Trender Backend Manager
cd /d "%~dp0..\.."

echo ========================================================
echo          Trender Backend 통합 실행 스크립트
echo ========================================================
echo.

:: 0. Redis (Docker) 기동 - 이미 떠 있으면 그대로 둠
echo [1/5] Redis(Docker) 확인 중...
docker compose -f "%~dp0..\..\..\docker-compose.yml" up -d redis
if errorlevel 1 (
    echo [경고] Redis를 못 띄웠습니다. Docker Desktop이 켜져 있는지 확인하세요.
    echo        Celery worker/beat는 Redis 없이는 동작하지 않습니다.
)
timeout /t 3 > nul

:: 1. Django 서버 실행 (새로운 터미널 창)
echo [2/5] Django 웹 서버를 시작하는 중...
start "Django Server" cmd /k "venv\Scripts\activate && python manage.py runserver"
timeout /t 2 > nul

:: 2. Celery 워커 실행 (새로운 터미널 창)
echo [3/5] Celery 워커를 시작하는 중...
start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A config worker -l info --pool=solo"
timeout /t 2 > nul

:: 3. Celery beat 실행 (새로운 터미널 창)
echo [4/5] Celery beat(스케줄러)를 시작하는 중...
start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A config beat -l info"
timeout /t 2 > nul

:: 4. ngrok 터널 실행 (새로운 터미널 창)
echo [5/5] ngrok 터널을 시작하는 중...
start "ngrok" cmd /k "ngrok http 8000"

echo.
echo ========================================================
echo   모든 서비스가 별도 창에서 실행되었습니다.
echo   ngrok 창에 새로 뜬 주소가 이전과 다르면(무료 플랜은 매번 바뀜),
echo   프론트(auth_service.dart의 baseUrl 등)를 그 주소로 갱신하세요.
echo.
echo   Celery beat에 KRX 종목/시세 동기화 + 관심종목 뉴스 수집(매시 정각,
echo   평일 09-16시)이 스케줄돼 있습니다. 지금 바로 실행하고 싶으면:
echo     Scripts\win\sync_krx.bat
echo     Scripts\win\collect_news.bat
echo.
echo   이 창은 닫으셔도 나머지는 백그라운드에서 유지됩니다.
echo ========================================================
echo.
pause