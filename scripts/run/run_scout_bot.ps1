# 정찰봇 실행 스크립트 (PowerShell)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptPath "..\.."
Set-Location $projectRoot
python test\scout_bot\day_main.py













