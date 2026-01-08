@echo off
chcp 65001 >nul
echo ========================================
echo 신호 수집 스케줄러 설정
echo ========================================
echo.

REM 현재 스크립트 위치에서 프로젝트 루트 찾기
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "BAT_FILE=%PROJECT_ROOT%\scripts\run\run_signals_collector.bat"
set "WORK_DIR=%PROJECT_ROOT%"

set TASK_NAME=SignalsCollector_Daily

echo 작업 이름: %TASK_NAME%
echo 스크립트 경로: %BAT_FILE%
echo 작업 디렉토리: %WORK_DIR%
echo.

REM 기존 작업이 있으면 삭제
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

REM 새 작업 생성 (매일 15:35 실행)
schtasks /Create /TN "%TASK_NAME%" /TR "\"%BAT_FILE%\"" /SC DAILY /ST 15:35 /RU SYSTEM /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo ✅ 스케줄러 설정 완료
    echo    작업 이름: %TASK_NAME%
    echo    실행 시간: 매일 15:35
    echo.
    echo 확인: schtasks /Query /TN "%TASK_NAME%"
) else (
    echo ❌ 스케줄러 설정 실패
    echo    관리자 권한이 필요할 수 있습니다.
)

echo.
pause







