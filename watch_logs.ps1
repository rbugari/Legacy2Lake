# Watch HTTP traffic logs in real-time

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  🔍 HTTP Traffic Monitor (DEBUG MODE)" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Watching: logs/http_traffic.log" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

$logFile = "logs\http_traffic.log"

# Create log file if it doesn't exist
if (!(Test-Path $logFile)) {
    New-Item -ItemType File -Path $logFile -Force | Out-Null
    Write-Host "✅ Created log file" -ForegroundColor Green
}

# Tail the log file
Get-Content $logFile -Wait -Tail 20
