@echo off
call "%~dp0_env.bat" || exit /b 1

echo 관심종목 뉴스 수집 (크롤링 + Gemini 분석 + 저장)
echo 기사 1건당 Gemini 호출이 있어 관심종목/기사 수에 따라 시간이 걸릴 수 있습니다.
python manage.py collect_news
if errorlevel 1 exit /b 1

echo.
echo 완료.
