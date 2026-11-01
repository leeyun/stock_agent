@echo off
REM Redis 준비 (manager.bat, dev.bat 공통). 직접 실행하지 않는다.
REM 6379 포트에 이미 Redis 컨테이너가 떠 있으면(다른 프로젝트 것 포함) 그대로 쓰고, 없으면 이 프로젝트 것을 띄운다.
set "REDIS_IN_USE="
for /f "delims=" %%n in ('docker ps --filter "publish=6379" --format "{{.Names}}" 2^>nul') do set "REDIS_IN_USE=%%n"
if defined REDIS_IN_USE (
    echo       6379 포트의 실행 중인 Redis 컨테이너를 사용합니다: %REDIS_IN_USE%
    exit /b 0
)
docker compose -f "%~dp0..\docker-compose.yml" up -d redis
