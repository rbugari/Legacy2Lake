# Test script to trigger debug logs
# Shows LLM calls, DB queries, and full execution details

$tenantId = "daac0ee6-3b28-412d-8acd-43ec51149188"
$projectId = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
$headers = @{ "X-Tenant-ID" = $tenantId }

Write-Host "🔍 Testing Debug Logs - Check Backend Window!" -ForegroundColor Cyan
Write-Host "=" -repeat 60

# Test 1: List projects (simple)
Write-Host "`n1️⃣  Fetching projects..." -ForegroundColor Yellow
try {
    $projects = Invoke-RestMethod -Uri "http://localhost:8085/projects" -Headers $headers -Method Get
    Write-Host "   ✅ Found $($projects.value.Count) projects" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Start-Sleep -Seconds 1

# Test 2: Get project details
Write-Host "`n2️⃣  Fetching project details..." -ForegroundColor Yellow
try {
    $project = Invoke-RestMethod -Uri "http://localhost:8085/projects/$projectId" -Headers $headers -Method Get
    Write-Host "   ✅ Project: $($project.name)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Start-Sleep -Seconds 1

# Test 3: Trigger Triage (this will show LLM logs!)
Write-Host "`n3️⃣  Running TRIAGE (Agent S) - Watch Backend Window for LLM logs!" -ForegroundColor Yellow
Write-Host "   ⏳ This will take 10-30 seconds..." -ForegroundColor Cyan
try {
    $body = @{ 
        system_prompt = $null
        user_context = $null 
    } | ConvertTo-Json
    
    $triage = Invoke-RestMethod `
        -Uri "http://localhost:8085/projects/$projectId/triage" `
        -Headers $headers `
        -Method Post `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "   ✅ Triage completed!" -ForegroundColor Green
    Write-Host "   📊 Check backend window for:" -ForegroundColor Cyan
    Write-Host "      • Agent S (Scout) execution" -ForegroundColor Gray
    Write-Host "      • LLM request/response" -ForegroundColor Gray
    Write-Host "      • Technology detection" -ForegroundColor Gray
    Write-Host "      • Database updates" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n" + ("=" -repeat 60)
Write-Host "✅ Test complete! Check Legacy2Lake API window for detailed logs" -ForegroundColor Green
