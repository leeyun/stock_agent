@echo off
chcp 65001 > nul
setlocal
call "%~dp0_backend.bat" || exit /b 1

echo [1/2] backend 테스트
python manage.py test
if errorlevel 1 exit /b 1

echo [2/2] frontend 정적 분석
cd /d "%~dp0..\frontend"
set "FLUTTER=flutter"
if exist ".fvmrc" set "FLUTTER=fvm flutter"
call %FLUTTER% analyze --no-fatal-infos
