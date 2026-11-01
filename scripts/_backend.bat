@echo off
REM 백엔드 스크립트 공통 준비: backend 폴더로 이동 + venv 활성화. 직접 실행하지 않는다.
cd /d "%~dp0..\backend"
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] backend\venv 가 없습니다. scripts\setup.bat 을 먼저 실행하세요.
    exit /b 1
)
if not exist ".env" (
    echo [ERROR] backend\.env 가 없습니다. scripts\setup.bat 을 먼저 실행하세요.
    exit /b 1
)
call venv\Scripts\activate.bat
