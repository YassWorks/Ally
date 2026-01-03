$ErrorActionPreference = "Stop"

Write-Host "=== Setting up Ally (Windows) ===" -ForegroundColor Cyan

# script directory
$InstallDir = $PSScriptRoot

# =========================== Step 1: Install requirements =================================

Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow

if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Error "uv not found. Please install it by running: irm https://astral.sh/uv/install.ps1 | iex"
    exit 1
}

Set-Location -Path $InstallDir

if (-not (Test-Path "pyproject.toml")) {
    uv init | Out-Null
}

cmd /c "uv add -q -r requirements.txt"

# =========================== Step 2: Create wrapper (ally.cmd) ============================

Write-Host "`nCreating launcher script..." -ForegroundColor Yellow

# wrapper script
$LauncherPath = Join-Path -Path $InstallDir -ChildPath "ally.bat"
$PythonPath = Join-Path -Path $InstallDir -ChildPath ".venv\Scripts\python.exe"
$MainScript = Join-Path -Path $InstallDir -ChildPath "main.py"

$BatchContent = "@echo off`r`n`"$PythonPath`" `"$MainScript`" %*"

Set-Content -Path $LauncherPath -Value $BatchContent
Write-Host "Launcher created at: $LauncherPath"

# =========================== Step 3: Add to PATH ==========================================

Write-Host "`nConfiguring PATH..." -ForegroundColor Yellow

# Get current User PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if the install directory is already in the PATH
if ($CurrentPath -split ';' -notcontains $InstallDir) {
    # Append the directory to the User PATH
    $NewPath = "$CurrentPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "Success! Added $InstallDir to your User PATH." -ForegroundColor Green
    Write-Host "NOTE: You must close and reopen your terminal for the 'ally' command to work." -ForegroundColor Magenta
} else {
    Write-Host "Path already configured." -ForegroundColor Green
    Write-Host "Setup complete! You can run 'ally' now. You may need to open a new terminal window." -ForegroundColor Green
}
