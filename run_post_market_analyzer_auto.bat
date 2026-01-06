@echo off
REM Post-Market Analyzer 자동 실행 스크립트 (그래프 포함)
REM 장 마감 후 자동으로 분석 및 그래프 생성
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=UTF-8

echo ========================================
echo Post-Market Analyzer 자동 실행
echo 그래프 포함 분석
echo ========================================
echo.

REM 오늘 날짜로 분석 실행 (그래프 포함)
python -m test.framework.analyzer.run_analyzer --with-graphs

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 분석 완료!
) else (
    echo.
    echo ❌ 분석 중 오류 발생
    exit /b 1
)

pause




