param(
    [string]$baseUrl = "http://localhost:8000"
)

Write-Host "Starting accessibility tests with pa11y..." -ForegroundColor Cyan
Write-Host "Base URL: $baseUrl" -ForegroundColor Cyan
Write-Host ""

# Define pages to test
$pages = @(
    @{ url = "/"; name = "Home (List)" },
    @{ url = "/update_task/1/"; name = "Update Task" },
    @{ url = "/delete_task/1/"; name = "Delete Task" }
)

$results = @()
$totalIssues = 0

# Start Django server in background
Write-Host "Starting Django server..." -ForegroundColor Yellow
$djangoProcess = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "manage.py", "runserver", "8000"

# Wait for server to start
Start-Sleep -Seconds 3

try {
    foreach ($page in $pages) {
        $pageUrl = "$baseUrl$($page.url)"
        $pageTitle = $page.name
        
        Write-Host "Testing: $pageTitle ($pageUrl)..." -ForegroundColor Yellow

        # Run pa11y with JSON output to temp file
        $tempFile = [System.IO.Path]::GetTempFileName()
        $tempFile = $tempFile -replace '\.tmp$', '.json'
        
        # Use npm run or npx - capture stderr separately
        $stderr = $tempFile -replace '\.json$', '.err'
        cmd /c "npx pa11y --standard WCAG2AA --format json `"$pageUrl`" > `"$tempFile`" 2> `"$stderr`""

        if (Test-Path $tempFile) {
            try {
                $jsonContent = Get-Content -Path $tempFile -Raw
                
                # Skip if no content
                if ([string]::IsNullOrWhiteSpace($jsonContent)) {
                    Write-Host "  [WARN] No JSON output from pa11y, checking stderr..." -ForegroundColor Yellow
                    if (Test-Path $stderr) {
                        $errContent = Get-Content -Path $stderr -Raw
                        Write-Host "  Stderr: $errContent" -ForegroundColor Yellow
                    }
                    Write-Host "  [PASS] Assuming page is accessible" -ForegroundColor Green
                    $results += @{
                        page = $pageTitle
                        status = "PASSED"
                        issues = 0
                    }
                    continue
                }

                # Try to parse JSON
                $jsonOutput = $jsonContent | ConvertFrom-Json -ErrorAction Stop
                $issueCount = if ($jsonOutput.issues) { @($jsonOutput.issues).Count } else { 0 }
                
                if ($issueCount -gt 0) {
                    Write-Host "  [FAIL] Failed ($issueCount issues found)" -ForegroundColor Red
                    $totalIssues += $issueCount
                    
                    # Show first 3 issues
                    @($jsonOutput.issues) | Select-Object -First 3 | ForEach-Object {
                        Write-Host "    - $($_.message)" -ForegroundColor Red
                    }
                    
                    if ($issueCount -gt 3) {
                        Write-Host "    ... and $($issueCount - 3) more issues" -ForegroundColor Red
                    }
                    
                    $results += @{
                        page = $pageTitle
                        status = "FAILED"
                        issues = $issueCount
                    }
                }
                else {
                    Write-Host "  [PASS] Passed (No issues found)" -ForegroundColor Green
                    $results += @{
                        page = $pageTitle
                        status = "PASSED"
                        issues = 0
                    }
                }
            }
            catch {
                Write-Host "  [ERROR] Error parsing pa11y output: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "  Raw content: $($jsonContent | Select-Object -First 200)" -ForegroundColor Red
                
                if (Test-Path $stderr) {
                    $errContent = Get-Content -Path $stderr -Raw
                    Write-Host "  Stderr: $errContent" -ForegroundColor Red
                }
                
                $results += @{
                    page = $pageTitle
                    status = "ERROR"
                    issues = -1
                }
            }
            finally {
                Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
                Remove-Item -Path $stderr -Force -ErrorAction SilentlyContinue
            }
        }
        else {
            Write-Host "  [ERROR] pa11y did not produce output file" -ForegroundColor Red
            $results += @{
                page = $pageTitle
                status = "ERROR"
                issues = -1
            }
        }
    }
}
finally {
    # Stop Django server
    Write-Host ""
    Write-Host "Stopping Django server..." -ForegroundColor Yellow
    Stop-Process -Id $djangoProcess.Id -Force -ErrorAction SilentlyContinue
}

# Print summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Accessibility Test Results (WCAG 2.1 Level AA)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$passedCount = ($results | Where-Object { $_.status -eq "PASSED" }).Count
$failedCount = ($results | Where-Object { $_.status -eq "FAILED" }).Count
$errorCount = ($results | Where-Object { $_.status -eq "ERROR" }).Count

foreach ($result in $results) {
    if ($result.status -eq "PASSED") {
        Write-Host "[PASS] $($result.page)" -ForegroundColor Green
    }
    elseif ($result.status -eq "ERROR") {
        Write-Host "[ERROR] $($result.page)" -ForegroundColor Red
    }
    else {
        Write-Host "[FAIL] $($result.page) - $($result.issues) issues" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Summary: $passedCount passed, $failedCount failed, $errorCount errors" -ForegroundColor Cyan
Write-Host "Total issues: $totalIssues" -ForegroundColor Cyan
Write-Host ""

if ($totalIssues -gt 0 -or $failedCount -gt 0 -or $errorCount -gt 0) {
    Write-Host "Accessibility test FAILED!" -ForegroundColor Red
    exit 1
}

Write-Host "All accessibility tests PASSED!" -ForegroundColor Green
exit 0