# ===============================
# Post-Market Analyzer 스케줄러 제거 스크립트
# ===============================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Post-Market Analyzer 스케줄러 제거" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$taskName = "Post-Market Analyzer 자동 실행"

# 작업 확인 (schtasks 사용)
$taskExists = schtasks /Query /TN $taskName 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  등록된 작업이 없습니다: $taskName" -ForegroundColor Yellow
    exit 0
}

# 작업 삭제 (schtasks 사용)
try {
    schtasks /Delete /TN $taskName /F | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 작업 스케줄러에서 제거 완료: $taskName" -ForegroundColor Green
    } else {
        throw "schtasks 삭제 실패"
    }
} catch {
    Write-Host "❌ 오류 발생: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 관리자 권한이 필요할 수 있습니다." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ 제거 완료!" -ForegroundColor Green







