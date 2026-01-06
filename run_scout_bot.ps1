# 정찰봇 실행 스크립트 (PowerShell)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
python test\scout_bot\day_main.py






