@echo off
chcp 65001 > nul
REM 관심종목 뉴스 수집 (네이버 검색 -> 본문 -> Gemini 분석 -> 저장). NAVER / GEMINI 키 필요.
REM 인자는 그대로 collect_news 에 전달된다. 예)
REM   collect_news.bat
REM   collect_news.bat --keywords 삼성전자 --per-keyword 3
REM   collect_news.bat --concurrency 2
call "%~dp0_backend.bat" || exit /b 1
python manage.py collect_news %*
