@echo off
call "%~dp0_env.bat" || exit /b 1
python manage.py runserver 0.0.0.0:8000