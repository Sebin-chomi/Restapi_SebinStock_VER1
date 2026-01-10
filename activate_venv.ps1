# ===============================
# 가상환경 활성화 PowerShell 스크립트
# ===============================

$ErrorActionPreference = "Stop"

# 현재 스크립트 위치 기준으로 프로젝트 루트 찾기
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptPath

# venv 경로
$venvPath = Join-Path $projectRoot "venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "오류: 가상환경을 찾을 수 없습니다: $activateScript" -ForegroundColor Red
    exit 1
}

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Green
& $activateScript

# 확인
Write-Host "가상환경이 활성화되었습니다." -ForegroundColor Green
Write-Host "Python 경로: $env:VIRTUAL_ENV\Scripts\python.exe" -ForegroundColor Cyan
python --version




