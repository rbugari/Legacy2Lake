# Quick restart script
Write-Host "🔄 Restarting services..." -ForegroundColor Cyan

# Kill all processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*UTM*"} | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*UTM*"} | Stop-Process -Force

Start-Sleep -Seconds 2

# Relaunch
python run.py

Write-Host "✅ Services restarted!" -ForegroundColor Green
