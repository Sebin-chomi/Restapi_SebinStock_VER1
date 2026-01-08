@echo off
REM Post-Market Analyzer 실행 스크립트
cd /d "%~dp0\..\.."
set PYTHONPATH=%~dp0\..\..

if "%1"=="" (
    python -m test.framework.analyzer.run_analyzer
) else (
    if "%2"=="--top100" (
        python -m test.framework.analyzer.run_analyzer %1 --top100
    ) else (
        python -m test.framework.analyzer.run_analyzer %1
    )
)

pause







