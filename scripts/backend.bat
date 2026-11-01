@echo off
chcp 65001 > nul
call "%~dp0_backend.bat" || exit /b 1

python manage.py migrate --check > nul 2>&1
if errorlevel 1 (
    echo 적용 안 된 마이그레이션이 있어 먼저 적용합니다.
    python manage.py migrate
    if errorlevel 1 exit /b 1
)

echo ============================================
echo   Trender Backend
echo   API 문서 : http://localhost:8000/api/docs/
echo   관리자   : http://localhost:8000/admin/
echo ============================================
python manage.py runserver 127.0.0.1:8000
