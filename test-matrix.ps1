param(
    [switch]$verbose
)

$pythonVersions = @("3.13", "3.9")
$djangoVersions = @("5.0", "4.2", "3.2")

$results = @()

Write-Host "Starting test matrix..." -ForegroundColor Cyan
Write-Host "Python versions: $($pythonVersions -join ', ')" -ForegroundColor Cyan
Write-Host "Django versions: $($djangoVersions -join ', ')" -ForegroundColor Cyan
Write-Host ""

foreach ($pythonVersion in $pythonVersions) {
    foreach ($djangoVersion in $djangoVersions) {
        $testName = "Python $pythonVersion + Django $djangoVersion"
        Write-Host "Testing: $testName..." -ForegroundColor Yellow

        # Create temporary Pipfile
        $pipfileContent = @"
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
django = "~=$djangoVersion"

[dev-packages]
ruff = "*"
coverage = "*"

[requires]
python_version = "$pythonVersion"
"@

        # Write temp Pipfile
        $pipfileContent | Set-Content "Pipfile.temp"

        # Install with pipenv
        & python -m pipenv --python $pythonVersion install --file Pipfile.temp 2>&1 | Out-Null

        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Installation failed" -ForegroundColor Red
            $results += @{
                test = $testName
                status = "FAILED"
                reason = "Installation"
            }
            continue
        }

        # Run linter
        & python -m pipenv run ruff check . 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Linter failed" -ForegroundColor Red
            $results += @{
                test = $testName
                status = "FAILED"
                reason = "Linter"
            }
            continue
        }

        # Run tests
        & python -m pipenv run python manage.py test 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Tests failed" -ForegroundColor Red
            $results += @{
                test = $testName
                status = "FAILED"
                reason = "Tests"
            }
            continue
        }

        # Check coverage
        & python -m pipenv run coverage run --source='tasks' manage.py test 2>&1 | Out-Null
        & python -m pipenv run coverage report 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Coverage check failed" -ForegroundColor Red
            $results += @{
                test = $testName
                status = "FAILED"
                reason = "Coverage"
            }
            continue
        }

        Write-Host "  ✓ Passed" -ForegroundColor Green
        $results += @{
            test = $testName
            status = "PASSED"
            reason = ""
        }
    }
}

# Clean up
Remove-Item "Pipfile.temp" -Force -ErrorAction SilentlyContinue

# Print summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Test Matrix Results" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

$passedCount = ($results | Where-Object { $_.status -eq "PASSED" }).Count
$failedCount = ($results | Where-Object { $_.status -eq "FAILED" }).Count

foreach ($result in $results) {
    if ($result.status -eq "PASSED") {
        Write-Host "✓ $($result.test)" -ForegroundColor Green
    }
    else {
        Write-Host "✗ $($result.test) - $($result.reason)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Summary: $passedCount passed, $failedCount failed" -ForegroundColor Cyan
Write-Host ""

if ($failedCount -gt 0) {
    exit 1
}
exit 0