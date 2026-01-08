@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Post-Market Pipeline 스케줄러 설정
echo ========================================
echo.

REM 프로젝트 루트
set "PROJECT_ROOT=C:\주식자동매매_개발관련\Restapi_SebinStock_VER1"
set "BAT_FILE=%PROJECT_ROOT%\scripts\run\run_post_market_pipeline.bat"
set "WORK_DIR=%PROJECT_ROOT%"

REM 작업 이름
set "TASK_NAME=PostMarketPipeline"

echo 작업 이름: %TASK_NAME%
echo 배치 파일: %BAT_FILE%
echo 작업 디렉토리: %WORK_DIR%
echo 실행 시간: 매일 15:35
echo.

REM 배치 파일 존재 확인
if not exist "%BAT_FILE%" (
    echo ❌ 오류: 배치 파일을 찾을 수 없습니다.
    echo    경로: %BAT_FILE%
    pause
    exit /b 1
)

echo ✅ 배치 파일 확인 완료
echo.

REM 기존 작업 삭제
echo 기존 작업 확인 중...
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ⚠️  기존 작업을 삭제합니다...
    schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ 기존 작업 삭제 완료
    )
)

REM 작업 스케줄러 등록
echo.
echo 📋 작업 스케줄러 등록 중...
echo.

schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /TR "\"%BAT_FILE%\"" ^
    /SC DAILY ^
    /ST 15:35 ^
    /RU "%USERNAME%" ^
    /RL HIGHEST ^
    /F ^
    /SD 01/01/2026 ^
    /ED 12/31/2099 ^
    /IT ^
    /CWD "%WORK_DIR%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 작업 스케줄러 등록 완료!
    echo.
    echo 📋 작업 정보:
    echo    이름: %TASK_NAME%
    echo    실행 시간: 매일 15:35
    echo    실행 파일: %BAT_FILE%
    echo    작업 디렉토리: %WORK_DIR%
    echo.
    echo 💡 확인 방법:
    echo    1. 작업 스케줄러 열기
    echo    2. 작업 스케줄러 라이브러리에서 '%TASK_NAME%' 확인
    echo.
    echo 💡 삭제 방법:
    echo    scripts\scheduler\remove_post_market_pipeline.bat 실행
    echo    또는: schtasks /Delete /TN "%TASK_NAME%" /F
) else (
    echo.
    echo ❌ 오류 발생
    echo.
    echo 💡 해결 방법:
    echo    1. 관리자 권한으로 실행
    echo    2. schtasks /Query /TN "%TASK_NAME%" 로 확인
    pause
    exit /b 1
)

echo.
echo ✅ 설정 완료!
pause

