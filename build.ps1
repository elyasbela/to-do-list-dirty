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
python -m pipenv run ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Linter failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "Linter passed" -ForegroundColor Green
Write-Host ""

# Run unit tests
Write-Host "Running unit tests..." -ForegroundColor Yellow
pipenv run python manage.py test tasks.tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "Tests passed" -ForegroundColor Green
Write-Host ""

# Run coverage
Write-Host "Running coverage tests..." -ForegroundColor Yellow
pipenv run coverage run manage.py test tasks.tests
pipenv run coverage report
if ($LASTEXITCODE -ne 0) {
    Write-Host "Coverage failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "Coverage passed" -ForegroundColor Green
Write-Host ""

# Run accessibility tests
Write-Host "Running accessibility tests..." -ForegroundColor Yellow
& .\test-accessibility.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Accessibility tests failed. Fix errors before building." -ForegroundColor Red
    exit 1
}
Write-Host "Accessibility tests passed" -ForegroundColor Green
Write-Host ""

# Update settings.py
$settingsPath = "todo\settings.py"
(Get-Content $settingsPath) -replace 'VERSION = .*', "VERSION = `"$version`"" | Set-Content $settingsPath
Write-Host "Updated VERSION in settings.py to $version" -ForegroundColor Green

# Stage and commit
git add todo\settings.py
git commit -m "chore: bump version to $version"
Write-Host "Committed version update" -ForegroundColor Green

# Tag
git tag -a "v$version" -m "Release version $version"
Write-Host "Tagged commit with v$version" -ForegroundColor Green

# Push tag to remote
git push origin "v$version"
Write-Host "Pushed tag to remote" -ForegroundColor Green

# Create zip
Compress-Archive -Path . -DestinationPath "todolist-$version.zip" -Force
Write-Host "Created zip: todolist-$version.zip" -ForegroundColor Green

Write-Host ""
$separator = "============================================================"
Write-Host $separator -ForegroundColor Cyan
Write-Host "Build complete! Version $version" -ForegroundColor Cyan
Write-Host $separator -ForegroundColor Cyan
exit 0