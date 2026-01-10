# ===============================
# Post-Market Analyzer 스케줄러 설정 스크립트 (간단 버전)
# ===============================
# Windows 작업 스케줄러에 17:00 자동 실행 등록

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Post-Market Analyzer 스케줄러 설정" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 현재 스크립트 위치에서 프로젝트 루트 찾기
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptDir "..\.."
$projectRoot = (Resolve-Path $projectRoot).Path
$batFileName = "run_post_market_analyzer_auto.bat"
$batFilePath = Join-Path $projectRoot "scripts\run\$batFileName"

# 절대 경로로 변환
$batFilePath = (Resolve-Path $batFilePath -ErrorAction Stop).Path

if (-not (Test-Path $batFilePath)) {
    Write-Host "❌ 오류: $batFileName 파일을 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "   현재 위치: $scriptDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 배치 파일 확인: $batFilePath" -ForegroundColor Green
Write-Host ""

# 작업 스케줄러 작업 이름
$taskName = "Post-Market Analyzer 자동 실행"

# 기존 작업이 있으면 삭제
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "⚠️  기존 작업을 삭제합니다..." -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host "✅ 기존 작업 삭제 완료" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  기존 작업 삭제 실패 (계속 진행): $_" -ForegroundColor Yellow
    }
}

# 작업 스케줄러 작업 생성
Write-Host "📋 작업 스케줄러 작업 생성 중..." -ForegroundColor Cyan

try {
    # 동작 정의
    $action = New-ScheduledTaskAction -Execute $batFilePath -WorkingDirectory $projectRoot
    
    # 트리거 정의 (매일 17:00)
    $trigger = New-ScheduledTaskTrigger -Daily -At "17:00"
    
    # 설정 정의
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # 주체 정의 (현재 사용자)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    
    # 작업 생성
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "장 마감 후 일일 분석 및 그래프 생성 (매일 17:00 자동 실행)" `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "✅ 작업 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 작업 정보:" -ForegroundColor Cyan
    Write-Host "   이름: $taskName" -ForegroundColor White
    Write-Host "   실행 시간: 매일 17:00" -ForegroundColor White
    Write-Host "   실행 파일: $batFilePath" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 확인 방법:" -ForegroundColor Yellow
    Write-Host "   1. 작업 스케줄러 열기" -ForegroundColor White
    Write-Host "   2. 작업 스케줄러 라이브러리에서 '$taskName' 확인" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 삭제 방법:" -ForegroundColor Yellow
    Write-Host "   작업 스케줄러에서 작업을 마우스 오른쪽 클릭 → 삭제" -ForegroundColor White
    Write-Host "   또는: remove_scheduler.bat 실행" -ForegroundColor White
    
} catch {
    Write-Host ""
    Write-Host "❌ 오류 발생: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 해결 방법:" -ForegroundColor Yellow
    Write-Host "   1. PowerShell을 관리자 권한으로 실행" -ForegroundColor White
    Write-Host "   2. 실행 정책 확인: Get-ExecutionPolicy" -ForegroundColor White
    Write-Host "   3. 실행 정책 변경: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "✅ 설정 완료!" -ForegroundColor Green











