@echo off
chcp 65001 > nul
call "%~dp0_backend.bat" || exit /b 1

echo [1/2] KRX 종목 마스터 동기화
python manage.py sync_krx_stocks
if errorlevel 1 exit /b 1

echo [2/2] KRX 시세 동기화
python manage.py sync_krx_quotes
