@echo off
call "%~dp0_env.bat" || exit /b 1

echo Celery worker 시작 (Redis가 떠 있어야 합니다)
celery -A config worker -l info --pool=solo
