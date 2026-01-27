# Script para iniciar el Backend API en el puerto correcto (8085)
# Convención: Todos los puertos terminan en 5

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  UTM Backend API - Puerto 8085" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Verificar si el puerto 8085 está ocupado
$port8085 = netstat -ano | findstr ":8085"
if ($port8085) {
    Write-Host "⚠️  Puerto 8085 está ocupado:" -ForegroundColor Yellow
    Write-Host $port8085
    Write-Host "`nDetén el proceso anterior antes de continuar." -ForegroundColor Yellow
    Write-Host "Usa: taskkill /PID <PID> /F`n" -ForegroundColor Yellow
    exit 1
}

# Cambiar al directorio del proyecto
Set-Location -Path "c:\proyectos_dev\UTM"

# Configurar variables de entorno
$env:PYTHONPATH = "apps/api"
$env:PORT = "8085"

Write-Host "✅ Configuración:" -ForegroundColor Green
Write-Host "   PYTHONPATH = apps/api" -ForegroundColor Gray
Write-Host "   PORT = 8085" -ForegroundColor Gray
Write-Host "`n🚀 Iniciando servidor..." -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8085" -ForegroundColor Green
Write-Host "   Docs: http://localhost:8085/docs" -ForegroundColor Green
Write-Host "`n⏹️  Presiona Ctrl+C para detener`n" -ForegroundColor Yellow

# Iniciar uvicorn
uvicorn apps.api.main:app --host 0.0.0.0 --port 8085 --reload
