@echo off
chcp 65001 > nul
setlocal
title Manager - Trender
REM 외부 공개용 올인원 관리 도구: Docker - Redis - ngrok - Django - Celery 순서로 실행
REM 서비스 창 제목은 모두 "Trender "로 시작한다 (메뉴 6번 종료 기능이 이 이름으로 찾음)
set "SCRIPTS=%~dp0"
set "ROOT=%~dp0.."
set "BACKEND=%~dp0..\backend"
set "WEB_BUILD=%~dp0..\frontend\build\web"
set "WAIT=%SystemRoot%\System32\timeout.exe"
set "DOCKER_DESKTOP=C:\Program Files\Docker\Docker\Docker Desktop.exe"

:MENU
cls
color 0B
echo ===================================================
echo   [Trender] Manager
echo ===================================================
echo   1. 전체 실행  Docker - Redis - ngrok - Django - Celery
echo   2. ngrok 공개 주소 확인
echo   3. 웹 빌드 (외부 공개용)
echo   4. 키 설정 상태 확인
echo   5. DB 마이그레이션 (makemigrations, migrate)
echo   6. 실행 중인 서비스 모두 종료
echo   7. 새 Django 앱 생성 (startapp)
echo   0. 나가기
echo ===================================================
set "choice="
set /p choice="번호를 입력하세요: "
if defined choice set "choice=%choice: =%"

if "%choice%"=="1" goto START_ALL
if "%choice%"=="2" goto SHOW_URL
if "%choice%"=="3" goto BUILD_WEB_MENU
if "%choice%"=="4" goto CHECK_KEYS
if "%choice%"=="5" goto MIGRATE
if "%choice%"=="6" goto STOP_ALL
if "%choice%"=="7" goto START_APP
if "%choice%"=="0" goto :EOF

echo 올바른 번호를 입력하세요.
"%WAIT%" /t 2 > nul
goto MENU


REM =========================================
REM 1. 전체 실행
REM =========================================
:START_ALL
cls
color 0A
call :LOAD_ENV
if not exist "%BACKEND%\venv\Scripts\python.exe" (
    echo [ERROR] backend\venv 가 없습니다. scripts\setup.bat 을 먼저 실행하세요.
    pause
    goto MENU
)

echo [1/6] Docker Desktop 확인
call :WAIT_DOCKER || goto START_FAILED

echo [2/6] Redis 컨테이너 시작
call "%SCRIPTS%_redis.bat" || goto START_FAILED

echo [3/6] ngrok 터널 시작
call :GET_NGROK_URL
if defined NGROK_URL (
    echo       이미 실행 중입니다.
) else if defined NGROK_DOMAIN (
    start "Trender ngrok" cmd /k ngrok http 8000 --url=https://%NGROK_DOMAIN%
) else (
    start "Trender ngrok" cmd /k ngrok http 8000
)

echo [4/6] 웹 빌드 확인
if exist "%WEB_BUILD%\.trender-public" (
    echo       외부 공개용 빌드가 있습니다. 코드를 바꿨다면 메뉴 3번으로 다시 빌드하세요.
) else (
    echo       외부 공개용 빌드가 없어 새로 빌드합니다. 1분 정도 걸립니다.
    call :BUILD_WEB || echo [경고] 웹 빌드에 실패했습니다. API는 동작하지만 웹 화면은 열리지 않습니다.
)

echo [5/6] Django 서버 시작
start "Trender Django" cmd /k call "%SCRIPTS%backend.bat"
"%WAIT%" /t 5 /nobreak > nul

echo [6/6] Celery worker, beat 시작
start "Trender Celery Worker" cmd /k call "%SCRIPTS%celery.bat" worker
start "Trender Celery Beat" cmd /k call "%SCRIPTS%celery.bat" beat

echo.
echo ngrok 주소를 확인하는 중...
for /l %%i in (1,1,10) do (
    call :GET_NGROK_URL
    if defined NGROK_URL goto START_DONE
    "%WAIT%" /t 2 /nobreak > nul
)
:START_DONE
call :PRINT_URL
pause
goto MENU

:START_FAILED
echo.
echo [ERROR] 실행을 중단했습니다. 위 메시지를 확인하세요.
pause
goto MENU


REM =========================================
REM 2. ngrok 공개 주소 확인
REM =========================================
:SHOW_URL
cls
call :GET_NGROK_URL
call :PRINT_URL
pause
goto MENU


REM =========================================
REM 3. 웹 빌드
REM =========================================
:BUILD_WEB_MENU
cls
color 0E
call :BUILD_WEB
if errorlevel 1 (
    echo [ERROR] 웹 빌드에 실패했습니다.
) else (
    echo 웹 빌드 완료. 실행 중인 Django가 새 빌드를 바로 서빙합니다. 브라우저에서 새로고침하세요.
)
pause
goto MENU


REM =========================================
REM 4. 키 설정 상태 확인
REM =========================================
:CHECK_KEYS
cls
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTS%_check_keys.ps1" "%BACKEND%\.env"
pause
goto MENU


REM =========================================
REM 5. DB 마이그레이션
REM =========================================
:MIGRATE
cls
color 0E
call "%SCRIPTS%migrate.bat"
echo.
pause
goto MENU


REM =========================================
REM 6. 서비스 종료
REM =========================================
:STOP_ALL
cls
color 0C
echo Trender 서비스 창을 종료합니다 (ngrok, Django, Celery).
taskkill /FI "WINDOWTITLE eq Trender*" /T /F > nul 2>&1
echo Redis 컨테이너를 중지합니다.
docker compose -f "%ROOT%\docker-compose.yml" stop redis > nul 2>&1
echo 완료. Docker Desktop은 그대로 둡니다.
pause
goto MENU


REM =========================================
REM 7. 새 Django 앱 생성
REM =========================================
:START_APP
cls
color 0D
set "app_name="
set /p app_name="생성할 앱 이름 (예: trender_agent, 취소는 엔터): "
if "%app_name%"=="" goto MENU
if exist "%BACKEND%\apps\%app_name%" (
    echo [ERROR] apps\%app_name% 이 이미 있습니다.
    pause
    goto MENU
)
pushd "%BACKEND%"
mkdir "apps\%app_name%"
venv\Scripts\python.exe manage.py startapp %app_name% "apps\%app_name%"
if errorlevel 1 (
    rd /s /q "apps\%app_name%"
    popd
    pause
    goto MENU
)
popd
echo.
echo apps\%app_name% 을 만들었습니다. 다음 두 가지를 직접 수정하세요.
echo   1. apps\%app_name%\apps.py 의 name 을 "apps.%app_name%" 로 변경
echo   2. config\settings.py 의 INSTALLED_APPS 에 "apps.%app_name%" 추가
pause
goto MENU


REM =========================================
REM 내부 함수
REM =========================================

REM backend\.env 에서 ngrok 설정만 읽는다. NGROK_AUTHTOKEN 은 ngrok이 환경변수로 직접 읽는다.
:LOAD_ENV
set "NGROK_DOMAIN="
if not exist "%BACKEND%\.env" exit /b 0
for /f "usebackq eol=# tokens=1,* delims==" %%a in ("%BACKEND%\.env") do (
    if /i "%%a"=="NGROK_DOMAIN" set "NGROK_DOMAIN=%%b"
    if /i "%%a"=="NGROK_AUTHTOKEN" if not "%%b"=="" set "NGROK_AUTHTOKEN=%%b"
)
if defined NGROK_DOMAIN set "NGROK_DOMAIN=%NGROK_DOMAIN:https://=%"
exit /b 0

REM Docker 엔진이 응답할 때까지 최대 120초 기다린다. 꺼져 있으면 Docker Desktop을 실행한다.
:WAIT_DOCKER
docker info > nul 2>&1
if not errorlevel 1 exit /b 0
if not exist "%DOCKER_DESKTOP%" (
    echo [ERROR] Docker Desktop을 찾을 수 없습니다: %DOCKER_DESKTOP%
    exit /b 1
)
echo       Docker Desktop을 시작합니다. 엔진 준비까지 최대 120초 기다립니다.
start "" "%DOCKER_DESKTOP%"
for /l %%i in (1,1,24) do (
    "%WAIT%" /t 5 /nobreak > nul
    docker info > nul 2>&1 && exit /b 0
)
echo [ERROR] Docker 엔진이 120초 안에 준비되지 않았습니다.
exit /b 1

REM ngrok 로컬 API(4040)에서 https 공개 주소를 읽어 NGROK_URL 에 넣는다.
:GET_NGROK_URL
set "NGROK_URL="
for /f "usebackq delims=" %%u in (`powershell -NoProfile -Command "try { $t = (Invoke-RestMethod -TimeoutSec 2 http://127.0.0.1:4040/api/tunnels).tunnels; ($t.Where({ $_.proto -eq 'https' }) + $t)[0].public_url } catch {}"`) do set "NGROK_URL=%%u"
exit /b 0

:PRINT_URL
echo ===================================================
if not defined NGROK_URL (
    echo   ngrok 주소를 찾을 수 없습니다. "Trender ngrok" 창의 오류를 확인하세요.
    echo ===================================================
    exit /b 0
)
echo   외부 주소  : %NGROK_URL%
echo   API 문서   : %NGROK_URL%/api/docs/
echo   관리자     : %NGROK_URL%/admin/
echo ===================================================
echo   Google 로그인을 쓰려면 위 외부 주소를 Google OAuth의
echo   승인된 JavaScript 원본에 등록해야 합니다.
exit /b 0

REM API_BASE_URL을 비워 빌드하면 웹이 자기 주소의 API를 호출한다 (Django가 웹과 API를 같이 서빙).
:BUILD_WEB
pushd "%ROOT%\frontend"
set "FLUTTER=flutter"
if exist ".fvmrc" set "FLUTTER=fvm flutter"
call %FLUTTER% build web --release --dart-define=API_BASE_URL=
set "BUILD_RC=%errorlevel%"
popd
if not "%BUILD_RC%"=="0" exit /b 1
echo public> "%WEB_BUILD%\.trender-public"
exit /b 0
