@echo off
REM Post-Market Analyzer 스케줄러 제거 스크립트

chcp 65001 >nul

echo ========================================
echo Post-Market Analyzer 스케줄러 제거
echo ========================================
echo.

set "TASK_NAME=Post-Market Analyzer 자동 실행"

REM 작업 확인
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  등록된 작업이 없습니다: %TASK_NAME%
    pause
    exit /b 0
)

REM 작업 삭제
echo 작업 삭제 중...
schtasks /Delete /TN "%TASK_NAME%" /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 작업 스케줄러에서 제거 완료: %TASK_NAME%
) else (
    echo.
    echo ❌ 오류 발생
    echo 💡 관리자 권한이 필요할 수 있습니다.
)

pause











