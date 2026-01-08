@echo off
REM Post-Market Analyzer 스케줄러 설정 스크립트
REM Windows 작업 스케줄러에 17:00 자동 실행 등록

REM schtasks.exe를 사용하는 버전으로 실행 (한글 경로 문제 해결)
call "%~dp0setup_scheduler_schtasks.bat"




