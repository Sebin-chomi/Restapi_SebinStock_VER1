@echo off
REM 정찰 결과 간단 확인 스크립트
cd /d "%~dp0"
set PYTHONPATH=%~dp0

if "%1"=="" (
    python -m test.framework.analyzer.view_scout_results
) else (
    python -m test.framework.analyzer.view_scout_results %1
)

pause




