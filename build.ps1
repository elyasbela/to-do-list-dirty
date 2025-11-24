param(
    [Parameter(Mandatory=$true)]
    [string]$version
)

if (-not $version) {
    Write-Host "Usage: .\build.ps1 -version 1.0.1"
    exit 1
}

Write-Host "Building version $version..." -ForegroundColor Cyan
Write-Host ""

# Run linter
Write-Host "Running Ruff linter..." -ForegroundColor Yellow
pipenv run ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Linter failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Linter passed" -ForegroundColor Green
Write-Host ""

# Run unit tests
Write-Host "Running unit tests..." -ForegroundColor Yellow
pipenv run python manage.py test
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Tests failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Tests passed" -ForegroundColor Green
Write-Host ""

# Run coverage
Write-Host "Running coverage tests..." -ForegroundColor Yellow
pipenv run coverage run --source='tasks' manage.py test
pipenv run coverage report
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Coverage failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Coverage passed" -ForegroundColor Green
Write-Host ""

# Run accessibility tests
Write-Host "Running accessibility tests..." -ForegroundColor Yellow
& .\test-accessibility.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Accessibility tests failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Accessibility tests passed" -ForegroundColor Green
Write-Host ""

# Update settings.py
$settingsPath = "todo\settings.py"
(Get-Content $settingsPath) -replace 'VERSION = .*', "VERSION = `"$version`"" | Set-Content $settingsPath
Write-Host "✓ Updated VERSION in settings.py to $version" -ForegroundColor Green

# Stage and commit
git add todo\settings.py
git commit -m "chore: bump version to $version"
Write-Host "✓ Committed version update" -ForegroundColor Green

# Tag
git tag -a "v$version" -m "Release version $version"
Write-Host "✓ Tagged commit with v$version" -ForegroundColor Green

# Push tag to remote
git push origin "v$version"
Write-Host "✓ Pushed tag to remote" -ForegroundColor Green

# Create zip
Compress-Archive -Path . -DestinationPath "todolist-$version.zip" -Force
Write-Host "✓ Created zip: todolist-$version.zip" -ForegroundColor Green

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Build complete! Version $version" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
exit 0