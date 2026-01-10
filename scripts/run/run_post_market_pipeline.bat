@echo off
setlocal enabledelayedexpansion

REM ===============================
REM 프로젝트 루트 설정
REM ===============================
set PROJECT_ROOT=C:\주식자동매매_개발관련\Restapi_SebinStock_VER1
set VENV_PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe

REM 로그 디렉토리
set LOG_DIR=%PROJECT_ROOT%\logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 날짜 형식: YYYYMMDD (wmic 사용)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TODAY=%datetime:~0,8%
set LOG_FILE=%LOG_DIR%\post_market_%TODAY%.log

echo ====================================== >> "%LOG_FILE%"
echo [START] Post Market Pipeline %DATE% %TIME% >> "%LOG_FILE%"
echo ====================================== >> "%LOG_FILE%"

cd /d "%PROJECT_ROOT%"

REM ===============================
REM 1️⃣ 대기실장봇
REM ===============================
echo [1] WaitingRoomManager >> "%LOG_FILE%"
"%VENV_PYTHON%" scout_selector\build_candidate_pool.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [FAIL] WaitingRoomManager >> "%LOG_FILE%"
    exit /b 1
)
echo [SUCCESS] WaitingRoomManager >> "%LOG_FILE%"

REM ===============================
REM 2️⃣ 캔들기록봇
REM ===============================
echo [2] OHLCVCollector >> "%LOG_FILE%"
"%VENV_PYTHON%" scout_selector\collect_ohlcv.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [FAIL] OHLCVCollector >> "%LOG_FILE%"
    exit /b 1
)
echo [SUCCESS] OHLCVCollector >> "%LOG_FILE%"

REM ===============================
REM 2.5️⃣ 종목선정회의 (MarketContext)
REM ===============================
echo [2.5] MarketContext >> "%LOG_FILE%"
"%VENV_PYTHON%" scout_selector\market_context.py --date %TODAY% --auto >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARN] MarketContext >> "%LOG_FILE%"
    REM 종목선정회의 실패는 파이프라인을 중단하지 않음 (문지기봇은 정상 동작)
) else (
    echo [SUCCESS] MarketContext >> "%LOG_FILE%"
)

REM ===============================
REM 3️⃣ 문지기봇
REM ===============================
echo [3] Gatekeeper >> "%LOG_FILE%"
"%VENV_PYTHON%" scout_selector\prepare_tomorrow.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [FAIL] Gatekeeper >> "%LOG_FILE%"
    exit /b 1
)
echo [SUCCESS] Gatekeeper >> "%LOG_FILE%"

echo [SUCCESS] Pipeline Finished >> "%LOG_FILE%"
exit /b 0

