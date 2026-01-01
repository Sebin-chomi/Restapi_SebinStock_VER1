# 가상환경 설정 스크립트
# PowerShell에서 실행: .\setup_venv.ps1

Write-Host "가상환경 생성 중..." -ForegroundColor Green

# 기존 가상환경이 있으면 제거
if (Test-Path .venv) {
    Write-Host "기존 가상환경 제거 중..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
}

# 새 가상환경 생성
python -m venv .venv

if ($LASTEXITCODE -eq 0) {
    Write-Host "가상환경 생성 완료!" -ForegroundColor Green
    
    # 가상환경 활성화
    Write-Host "가상환경 활성화 중..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
    
    # pip 업그레이드
    Write-Host "pip 업그레이드 중..." -ForegroundColor Green
    python -m pip install --upgrade pip
    
    # 개발 도구 설치
    Write-Host "개발 도구 설치 중..." -ForegroundColor Green
    python -m pip install black autopep8 flake8
    
    Write-Host "`n설치 완료!" -ForegroundColor Green
    Write-Host "설치된 도구 확인:" -ForegroundColor Cyan
    python -m black --version
    python -m autopep8 --version
    python -m flake8 --version
    
} else {
    Write-Host "가상환경 생성 실패!" -ForegroundColor Red
    exit 1
}

