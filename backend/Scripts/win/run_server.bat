@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM ============================================================
REM  Trender - accounts 확인용 개발 서버 실행 스크립트
REM  위치: backend/run.bat
REM  실행: 더블클릭 또는 cmd에서 run.bat
REM ============================================================

set "PROJECT_DIR=C:\workspace\trender\backend"
cd /d "%PROJECT_DIR%"

set "HOST=127.0.0.1"
set "PORT=8000"
set "DOCS_URL=http://%HOST%:%PORT%/api/docs/"
set "DJANGO_SETTINGS_MODULE=config.settings"

echo.
echo ============================================
echo   Trender 개발 서버
echo ============================================
echo.

REM ---------- 1. 가상환경 ----------
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv 를 찾을 수 없습니다: %PROJECT_DIR%\venv
    echo         python -m venv venv 로 먼저 생성하세요.
    goto :fail
)

echo [1/5] 가상환경 활성화...
call "venv\Scripts\activate.bat"
if errorlevel 1 goto :fail

REM ---------- 2. 환경 파일 ----------
if not exist ".env" (
    echo [ERROR] .env 파일이 없습니다.
    echo         DJANGO_SECRET_KEY, POSTGRES_* 값을 설정하세요.
    goto :fail
)
echo [2/5] .env 확인 완료

REM ---------- 3. 마이그레이션 ----------
echo [3/5] 마이그레이션 확인...
python manage.py makemigrations
if errorlevel 1 goto :fail

python manage.py migrate
if errorlevel 1 (
    echo.
    echo [ERROR] migrate 실패. Postgres 컨테이너가 떠 있는지 확인하세요.
    echo         docker compose up -d db
    goto :fail
)

REM ---------- 4. 시스템 점검 ----------
echo [4/5] Django 설정 점검...
python manage.py check
if errorlevel 1 goto :fail

REM ---------- 5. 브라우저 예약 + 서버 기동 ----------
echo [5/5] 서버 기동 중...
echo.
echo   API 문서 : %DOCS_URL%
echo   스키마   : http://%HOST%:%PORT%/api/schema/
echo   관리자   : http://%HOST%:%PORT%/admin/
echo.
echo   종료: Ctrl+C
echo ============================================
echo.

start "" /b cmd /c "timeout /t 4 /nobreak > nul & start """" ""%DOCS_URL%"""

python manage.py runserver %HOST%:%PORT%

goto :eof

:fail
echo.
echo 실행이 중단되었습니다.
pause
exit /b 1