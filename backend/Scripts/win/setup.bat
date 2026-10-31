@echo off
cd /d "%~dp0..\.."

if not exist "venv" (
    echo [1/4] venv 생성
    python -m venv venv
)
call venv\Scripts\activate.bat

echo [2/4] 패키지 설치
pip install -r requirements.txt
if errorlevel 1 exit /b 1

if not exist ".env" (
    echo [!] .env 가 없습니다. .env.example 을 복사합니다.
    copy .env.example .env
    echo     KIS / NAVER 키를 채운 뒤 다시 실행하세요.
)

echo [3/4] DB 적용
python manage.py migrate
if errorlevel 1 exit /b 1

echo [4/4] 관리자 계정
python manage.py createsuperuser

echo.
echo 완료. scripts\dev.bat 으로 서버를 켜세요.