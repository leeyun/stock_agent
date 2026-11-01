@echo off
chcp 65001 > nul
setlocal
REM 최초 1회 셋업: backend venv/패키지/.env/DB/KRX 종목 + frontend 패키지
REM 다른 파이썬을 쓰려면: set PYTHON=C:\경로\python.exe 후 실행
if "%PYTHON%"=="" set "PYTHON=C:\development\python\python-3.12.10\python.exe"
set "ROOT=%~dp0.."

echo [1/6] backend venv
if exist "%ROOT%\backend\venv\Scripts\python.exe" goto :venv_ok
if not exist "%PYTHON%" (
    echo [ERROR] 파이썬을 찾을 수 없습니다: %PYTHON%
    echo         set PYTHON=경로\python.exe 로 지정한 뒤 다시 실행하세요.
    exit /b 1
)
"%PYTHON%" -m venv "%ROOT%\backend\venv"
if errorlevel 1 exit /b 1
:venv_ok

echo [2/6] backend 패키지 설치
"%ROOT%\backend\venv\Scripts\python.exe" -m pip install -r "%ROOT%\backend\requirements.txt"
if errorlevel 1 exit /b 1

echo [3/6] backend .env
if exist "%ROOT%\backend\.env" goto :env_ok
copy "%ROOT%\backend\.env.example" "%ROOT%\backend\.env" > nul
pushd "%ROOT%\backend"
venv\Scripts\python.exe -c "import pathlib; from django.core.management.utils import get_random_secret_key as gen; p = pathlib.Path('.env'); p.write_text(p.read_text(encoding='utf-8').replace('DJANGO_SECRET_KEY=change-me', 'DJANGO_SECRET_KEY=' + gen(), 1), encoding='utf-8')"
popd
echo       .env 를 만들고 DJANGO_SECRET_KEY 를 생성했습니다. NAVER / GEMINI 키는 직접 채우세요.
:env_ok

call "%~dp0_backend.bat" || exit /b 1

echo [4/6] DB 마이그레이션
python manage.py migrate
if errorlevel 1 exit /b 1

echo [5/6] KRX 종목 마스터 + 시세 동기화
python manage.py sync_krx_stocks
if errorlevel 1 exit /b 1
python manage.py sync_krx_quotes
if errorlevel 1 exit /b 1

echo [6/6] frontend 패키지
cd /d "%ROOT%\frontend"
set "FLUTTER=flutter"
if exist ".fvmrc" set "FLUTTER=fvm flutter"
call %FLUTTER% pub get
if errorlevel 1 exit /b 1

echo.
echo 셋업 완료. scripts\dev.bat 으로 백엔드와 웹을 켜세요.
echo 관리자 페이지가 필요하면: cd backend ^& venv\Scripts\python manage.py createsuperuser
