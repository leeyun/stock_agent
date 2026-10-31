@echo off
call "%~dp0_env.bat" || exit /b 1

echo [1/3] 마이그레이션 파일 생성
python manage.py makemigrations
if errorlevel 1 exit /b 1

echo.
echo [2/3] 적용 대기 목록
python manage.py showmigrations --plan | findstr /c:"[ ]"

echo.
echo [3/3] DB 적용
python manage.py migrate
if errorlevel 1 exit /b 1

echo.
echo 완료.