@echo off
chcp 65001 > nul
REM 개발 환경 한 번에 켜기 (각각 새 창)
REM   dev.bat           백엔드 + 웹
REM   dev.bat celery    위 + Redis(Docker) + Celery worker/beat (KRX 시세, 뉴스 자동 수집)
set "SCRIPTS=%~dp0"

if /i not "%~1"=="celery" goto :apps
echo Redis 시작 (Docker)...
call "%SCRIPTS%_redis.bat"
if errorlevel 1 (
    echo [경고] Redis를 띄우지 못했습니다. Docker Desktop이 켜져 있는지 확인하세요.
) else (
    start "Celery Worker" cmd /k call "%SCRIPTS%celery.bat" worker
    start "Celery Beat" cmd /k call "%SCRIPTS%celery.bat" beat
)

:apps
start "Trender Backend" cmd /k call "%SCRIPTS%backend.bat"
start "Trender Web" cmd /k call "%SCRIPTS%web.bat"

echo 각 서비스가 별도 창에서 실행됩니다. 종료는 각 창에서 Ctrl+C.
