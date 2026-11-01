@echo off
chcp 65001 > nul
call "%~dp0_backend.bat" || exit /b 1

echo [1/2] 마이그레이션 파일 생성
python manage.py makemigrations
if errorlevel 1 exit /b 1

echo [2/2] DB 적용
python manage.py migrate
