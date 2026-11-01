@echo off
chcp 65001 > nul
call "%~dp0_backend.bat" || exit /b 1

echo ============================================
echo  backend\db.sqlite3 를 삭제하고 새로 만듭니다.
echo  계정, 관심종목, 뉴스 데이터는 복구되지 않습니다.
echo ============================================
set /p CONFIRM="계속하려면 RESET 입력: "
if /i not "%CONFIRM%"=="RESET" (
    echo 취소했습니다.
    exit /b 0
)

echo [1/3] DB 삭제
if exist "db.sqlite3" del /q "db.sqlite3"

echo [2/3] 마이그레이션 적용
python manage.py migrate
if errorlevel 1 exit /b 1

echo [3/3] KRX 종목 마스터 + 시세 동기화
python manage.py sync_krx_stocks
if errorlevel 1 exit /b 1
python manage.py sync_krx_quotes
