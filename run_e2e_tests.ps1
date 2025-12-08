# run_e2e_tests.ps1 - Run all E2E Selenium tests
param(
    [string]$ServerUrl = "http://127.0.0.1:8000",
    [int]$ServerStartupWait = 5
)

Write-Host "`n=== E2E Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# Check if server is already running
Write-Host "Checking if server is running on $ServerUrl..." -ForegroundColor Yellow
$serverAlreadyRunning = $false

try {
    $null = Invoke-WebRequest -Uri $ServerUrl -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    $serverAlreadyRunning = $true
    Write-Host "[OK] Server is already running" -ForegroundColor Green
}
catch {
    Write-Host "[INFO] Server is not running" -ForegroundColor Yellow
}

$serverJob = $null

try {
    # Start Django server if needed
    if (-not $serverAlreadyRunning) {
        Write-Host "`nStarting Django server..." -ForegroundColor Yellow
        
        # Extract host and port from URL
        $uri = [System.Uri]$ServerUrl
        $serverHost = $uri.Host
        $serverPort = $uri.Port
        
        Write-Host "Server will run on ${serverHost}:${serverPort}" -ForegroundColor Gray
        
        # Start server in background job
        $serverJob = Start-Job -ScriptBlock {
            param($projectPath, $serverHost, $serverPort)
            Set-Location $projectPath
            & pipenv run python manage.py runserver "${serverHost}:${serverPort}" 2>&1
        } -ArgumentList $PWD, $serverHost, $serverPort
        
        Write-Host "Waiting ${ServerStartupWait}s for server to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds $ServerStartupWait
        
        # Check if server job is still running
        $jobState = (Get-Job -Id $serverJob.Id).State
        if ($jobState -ne "Running") {
            Write-Host "`n[ERROR] Server job failed to start!" -ForegroundColor Red
            Write-Host "`nJob output:" -ForegroundColor Yellow
            Receive-Job -Job $serverJob
            throw "Server startup failed"
        }
        
        # Verify server is responding
        $maxRetries = 5
        $serverReady = $false
        
        for ($i = 1; $i -le $maxRetries; $i++) {
            try {
                Write-Host "Checking server readiness (attempt $i/$maxRetries)..." -ForegroundColor Gray
                $null = Invoke-WebRequest -Uri $ServerUrl -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
                $serverReady = $true
                Write-Host "[OK] Server is ready!" -ForegroundColor Green
                break
            }
            catch {
                if ($i -lt $maxRetries) {
                    Start-Sleep -Seconds 2
                }
            }
        }
        
        if (-not $serverReady) {
            Write-Host "`n[ERROR] Server did not become ready in time" -ForegroundColor Red
            Write-Host "`nServer job output:" -ForegroundColor Yellow
            Receive-Job -Job $serverJob
            throw "Server not responding"
        }
    }
    
    # Run E2E tests
    Write-Host "`nRunning Selenium E2E tests..." -ForegroundColor Cyan
    Write-Host "================================`n" -ForegroundColor Cyan
    
    $allTestsPassed = $true
    
    # Test 1: TC016 - CRUD Complete Cycle
    Write-Host "`n[TEST 1/2] Running TC016 - CRUD Complete Cycle..." -ForegroundColor Yellow
    & pipenv run python tasks/test_e2e_selenium.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] TC016 failed!" -ForegroundColor Red
        $allTestsPassed = $false
    }
    else {
        Write-Host "[PASS] TC016 passed!" -ForegroundColor Green
    }
    
    # Test 2: TC017 - Cross Impact Verification
    Write-Host "`n[TEST 2/2] Running TC017 - Cross Impact Verification..." -ForegroundColor Yellow
    & pipenv run python tasks/test_e2e_cross_impact.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] TC017 failed!" -ForegroundColor Red
        $allTestsPassed = $false
    }
    else {
        Write-Host "[PASS] TC017 passed!" -ForegroundColor Green
    }
    
    # Summary
    Write-Host "`n" + "="*70 -ForegroundColor Cyan
    Write-Host "E2E TEST SUITE SUMMARY" -ForegroundColor Cyan
    Write-Host "="*70 -ForegroundColor Cyan
    
    if ($allTestsPassed) {
        Write-Host "[PASS] All E2E tests passed!" -ForegroundColor Green
        $exitCode = 0
    }
    else {
        Write-Host "[FAIL] Some E2E tests failed!" -ForegroundColor Red
        $exitCode = 1
    }
    
    Write-Host "`nCheck result_test_selenium.json for detailed results" -ForegroundColor Cyan
    
    exit $exitCode
}
catch {
    Write-Host "`n[ERROR] $_" -ForegroundColor Red
    
    # Show server logs if available
    if ($serverJob) {
        Write-Host "`nServer logs:" -ForegroundColor Yellow
        Receive-Job -Job $serverJob
    }
    
    exit 1
}
finally {
    # Cleanup: Stop server if we started it
    if ($serverJob) {
        Write-Host "`nStopping Django server..." -ForegroundColor Yellow
        Stop-Job $serverJob -ErrorAction SilentlyContinue
        Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Server stopped" -ForegroundColor Green
    }
}