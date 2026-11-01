@echo off
chcp 65001 > nul
cd /d "%~dp0..\frontend"

REM FVM으로 프로젝트 전용 Flutter 버전을 잡아둔 경우(.fvmrc) 그 버전을 사용
set "FLUTTER=flutter"
if exist ".fvmrc" set "FLUTTER=fvm flutter"

REM 다른 백엔드에 붙일 때: set API_BASE_URL=https://api.example.com 후 실행
if "%API_BASE_URL%"=="" set "API_BASE_URL=http://localhost:8000"

echo ============================================
echo   Trender Web (Chrome)
echo   Flutter : %FLUTTER%
echo   API     : %API_BASE_URL%
echo   주소    : http://localhost:3000
echo ============================================
call %FLUTTER% run -d chrome --web-port 3000 --dart-define=API_BASE_URL=%API_BASE_URL%
