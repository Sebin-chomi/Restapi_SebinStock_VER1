@echo off
REM 정찰봇 실행 스크립트
cd /d "%~dp0"
set PYTHONPATH=%CD%
python test\scout_bot\day_main.py
pause

