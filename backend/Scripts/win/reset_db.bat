@echo off
call "%~dp0_env.bat" || exit /b 1

echo ============================================
echo  DB와 마이그레이션 파일을 전부 삭제합니다.
echo  데이터는 복구되지 않습니다.
echo ============================================
set /p CONFIRM="계속하려면 RESET 입력: "
if /i not "%CONFIRM%"=="RESET" (
    echo 취소했습니다.
    exit /b 0
)

echo [1/6] 마이그레이션 파일 삭제
for /d %%d in (apps\*) do (
    if exist "%%d\migrations" (
        for %%f in ("%%d\migrations\*.py") do (
            if /i not "%%~nxf"=="__init__.py" del /q "%%f"
        )
        if exist "%%d\migrations\__pycache__" rd /s /q "%%d\migrations\__pycache__"
    )
)

echo [2/6] DB 삭제
REM --- SQLite ---
if exist "db.sqlite3" del /q "db.sqlite3"
REM --- PostgreSQL 이면 위 줄 대신 아래 두 줄 사용 ---
REM dropdb -U postgres trender
REM createdb -U postgres trender

echo [3/6] 마이그레이션 재생성
python manage.py makemigrations trender_auth trender_stock trender_news trender_watchlist trender_digest
if errorlevel 1 exit /b 1

echo [4/6] 적용
python manage.py migrate
if errorlevel 1 exit /b 1

echo [5/6] KRX 종목 마스터 동기화
python manage.py sync_krx_stocks
if errorlevel 1 exit /b 1

echo [6/6] KRX 시세 동기화
python manage.py sync_krx_quotes
if errorlevel 1 exit /b 1

echo.
echo 완료. 관리자 계정이 필요하면 아래 명령을 따로 실행하세요.
echo   python manage.py createsuperuser