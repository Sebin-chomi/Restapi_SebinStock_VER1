@echo off
chcp 65001 >nul
echo ========================================
echo 신호 수집 실행
echo ========================================
echo.

cd /d "%~dp0\..\.."
python signals_collector/run_collect.py

echo.
echo ========================================
echo 신호 수집 완료
echo ========================================
pause







