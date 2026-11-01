@echo off
chcp 65001 > nul
REM 사용법: celery.bat worker ^| beat   (둘 다 떠 있어야 스케줄 작업이 실제로 처리됨, Redis 필요)
if /i "%~1"=="worker" goto :run
if /i "%~1"=="beat" goto :run
echo 사용법: scripts\celery.bat worker ^| beat
exit /b 1

:run
call "%~dp0_backend.bat" || exit /b 1
if /i "%~1"=="worker" (
    celery -A config worker -l info --pool=solo
) else (
    celery -A config beat -l info
)
