@echo off
cd /d "%~dp0..\.."
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv를 찾을 수 없습니다. backend/venv 가 맞는지 확인하세요.
    exit /b 1
)
call venv\Scripts\activate.bat