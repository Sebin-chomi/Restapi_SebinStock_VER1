@echo off
REM ===============================
REM 가상환경 활성화 배치 파일
REM ===============================
call venv\Scripts\activate.bat
echo 가상환경이 활성화되었습니다.
echo Python 경로: %VIRTUAL_ENV%\Scripts\python.exe
python --version
cmd /k




