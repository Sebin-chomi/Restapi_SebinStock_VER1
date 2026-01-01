@echo off
chcp 65001 >nul
echo 가상환경 생성 중...

REM 기존 가상환경이 있으면 제거
if exist .venv (
    echo 기존 가상환경 제거 중...
    rmdir /s /q .venv
)

REM 새 가상환경 생성
python -m venv .venv

if %ERRORLEVEL% EQU 0 (
    echo 가상환경 생성 완료!
    
    REM 가상환경 활성화
    echo 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
    
    REM pip 업그레이드
    echo pip 업그레이드 중...
    python -m pip install --upgrade pip
    
    REM 개발 도구 설치
    echo 개발 도구 설치 중...
    python -m pip install black autopep8 flake8
    
    echo.
    echo 설치 완료!
    echo 설치된 도구 확인:
    python -m black --version
    python -m autopep8 --version
    python -m flake8 --version
    
) else (
    echo 가상환경 생성 실패!
    pause
    exit /b 1
)

pause

