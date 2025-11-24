param(
    [Parameter(Mandatory=$true)]
    [string]$version
)

if (-not $version) {
    Write-Host "Usage: .\build.ps1 -version 1.0.1"
    exit 1
}

Write-Host "Building version $version..."

# Update settings.py
$settingsPath = "todo\settings.py"
(Get-Content $settingsPath) -replace 'VERSION = .*', "VERSION = `"$version`"" | Set-Content $settingsPath
Write-Host "✓ Updated VERSION in settings.py to $version"

# Stage and commit
git add todo\settings.py
git commit -m "chore: bump version to $version"
Write-Host "✓ Committed version update"

# Tag
git tag -a "v$version" -m "Release version $version"
Write-Host "✓ Tagged commit with v$version"

# Create zip
Compress-Archive -Path . -DestinationPath "todolist-$version.zip" -Force
Write-Host "✓ Created zip: todolist-$version.zip"

Write-Host ""
Write-Host "Build complete! Version $version"