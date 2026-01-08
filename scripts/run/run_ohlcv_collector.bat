@echo off
chcp 65001 >nul
echo ========================================
echo 캔들기록봇 실행
echo ========================================
echo.

cd /d "%~dp0\..\.."
python scout_selector\collect_ohlcv.py %*

echo.
echo ========================================
echo 캔들기록봇 실행 완료
echo ========================================
pause







