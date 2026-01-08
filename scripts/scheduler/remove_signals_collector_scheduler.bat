@echo off
chcp 65001 >nul
echo ========================================
echo 신호 수집 스케줄러 제거
echo ========================================
echo.

set TASK_NAME=SignalsCollector_Daily

echo 작업 이름: %TASK_NAME%
echo.

schtasks /Delete /TN "%TASK_NAME%" /F

if %ERRORLEVEL% EQU 0 (
    echo ✅ 스케줄러 제거 완료
) else (
    echo ⚠️  작업이 존재하지 않거나 제거 실패
)

echo.
pause







