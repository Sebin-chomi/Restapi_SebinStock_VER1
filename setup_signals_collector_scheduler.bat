@echo off
chcp 65001 >nul
echo ========================================
echo 신호 수집 스케줄러 설정
echo ========================================
echo.

set TASK_NAME=SignalsCollector_Daily
set SCRIPT_PATH=%~dp0run_signals_collector.bat
set WORK_DIR=%~dp0

echo 작업 이름: %TASK_NAME%
echo 스크립트 경로: %SCRIPT_PATH%
echo 작업 디렉토리: %WORK_DIR%
echo.

REM 기존 작업이 있으면 삭제
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

REM 새 작업 생성 (매일 15:35 실행)
schtasks /Create /TN "%TASK_NAME%" /TR "\"%SCRIPT_PATH%\"" /SC DAILY /ST 15:35 /RU SYSTEM /RL HIGHEST /F

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




