@echo off
call "%~dp0_env.bat" || exit /b 1

echo Celery beat 시작 (KRX 종목/시세 스케줄 실행 - celery_worker.bat도 별도로 떠 있어야 실제로 처리됨)
celery -A config beat -l info
