@echo off
chcp 65001 >nul
echo ========================================
echo 대기실장봇 실행
echo ========================================
echo.

cd /d "%~dp0\..\.."
python scout_selector\build_candidate_pool.py %*

echo.
echo ========================================
echo 대기실장봇 실행 완료
echo ========================================
pause











