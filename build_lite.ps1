# ==============================================================================
# PySide6 App Build and Release Script
# - 仅编译 ： .\build_lite.ps1
# - 编译并发布 ： .\build_lite.ps1 -r
# - 跳过编译仅发布 ： .\build_lite.ps1 -r -s
# ==============================================================================

param (
    [Alias("r")]
    [switch]$release,    # If set, execute zip, git commit, and github release
    
    [Alias("s")]
    [switch]$skipBuild   # If set, skip Nuitka build and start from step 3 (zip/release)
)

# Set working directory to script location
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $PSScriptRoot

# Conda Environment Activation
$CONDA_ENV_NAME = "myenv"
$CONDA_PATH = "D:\ISoftware\miniconda\router"
$CONDA_BIN = "$CONDA_PATH\Scripts\conda.exe"
$ENV_PREFIX = "$CONDA_PATH\envs\$CONDA_ENV_NAME"
$ENV_PYTHON = "$ENV_PREFIX\python.exe"

if (Test-Path $ENV_PYTHON) {
    Write-Host "Activating conda environment: $CONDA_ENV_NAME" -ForegroundColor Cyan
    $env:PATH = "$ENV_PREFIX;$ENV_PREFIX\Scripts;$env:PATH"
    $env:CONDA_PREFIX = $ENV_PREFIX
    Write-Host "Using Python: $ENV_PYTHON" -ForegroundColor Green
} elseif (Test-Path $CONDA_BIN) {
    Write-Host "Activating via conda activate..." -ForegroundColor Cyan
    & $CONDA_BIN activate $CONDA_ENV_NAME
} else {
    Write-Host "Conda not found. Using system Python." -ForegroundColor DarkYellow
}

# 1. Extract Version and APP_NAME from core/constants.py
$ConstFile = "core/constants.py"
$VersionRegex = 'APP_VERSION\s*=\s*"([^"]+)"'
$AppNameRegex = 'APP_NAME\s*=\s*"([^"]+)"'
$ConstContent = Get-Content $ConstFile -Raw

if ($ConstContent -match $VersionRegex) {
    $APP_VERSION = $matches[1]
    Write-Host "Found APP_VERSION in ${ConstFile}: v$APP_VERSION" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find APP_VERSION in $ConstFile" -ForegroundColor Red
    Pop-Location
    Exit 1
}

if ($ConstContent -match $AppNameRegex) {
    $APP_NAME = $matches[1]
    Write-Host "Found APP_NAME in ${ConstFile}: $APP_NAME" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find APP_NAME in $ConstFile" -ForegroundColor Red
    Pop-Location
    Exit 1
}

$MainFile = "main.py"
$OUTPUT_DIR = "output"
$TAG_NAME = "v$APP_VERSION"

# Set Nuitka cache directory to a local folder to keep the system clean
$env:NUITKA_CACHE_DIR = "nuitka_cache"

Write-Host "Starting optimized build for $APP_NAME v$APP_VERSION..." -ForegroundColor Cyan

# Check if output directory exists, if not create it
if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR | Out-Null
}

# 2. Run Nuitka Build (Optimized for size)
if ($skipBuild) {
    Write-Host "Skipping Nuitka build step as requested." -ForegroundColor Cyan
} else {
    Write-Host "Building executable with Nuitka..." -ForegroundColor Yellow
    python -m nuitka `
        --standalone `
        --windows-console-mode=attach `
        --enable-plugin=pyside6 `
        --include-qt-plugins=sensible,styles `
        --windows-icon-from-ico=assets/logo.ico `
        --include-data-dir=assets=assets `
        --include-data-dir=config=config `
        --include-data-dir=database=database `
        --output-dir=$OUTPUT_DIR `
        --output-filename=$APP_NAME `
        --assume-yes-for-downloads `
        --jobs=8 `
        --python-flag=-OO `
        --lto=no `
        --nofollow-import-to=numpy,scipy,pandas,matplotlib,IPython,PIL,tkinter,PyQt6,PyQt5 `
        --noinclude-dlls=*.pdb `
        --remove-output `
        $MainFile

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed! Exiting." -ForegroundColor Red
        Pop-Location
        Exit 1
    }

    Write-Host "Build completed successfully!" -ForegroundColor Green
}

if (-not $release) {
    Write-Host "No --release flag detected. Skipping zip, git commit, and GitHub release steps." -ForegroundColor Cyan
    Write-Host "All tasks completed!" -ForegroundColor Green
    Pop-Location
    Exit 0
}

# 3. Zip the output for Release
$ZipFileName = "$APP_NAME-$TAG_NAME-Windows.zip"
$ZipFilePath = Join-Path $OUTPUT_DIR "$ZipFileName"
$SourceDir = Join-Path $OUTPUT_DIR "main.dist"

if (-not (Test-Path $SourceDir)) {
    Write-Host "Error: Build output not found at $SourceDir" -ForegroundColor Red
    Pop-Location
    Exit 1
}

if (Test-Path $ZipFilePath) {
    Remove-Item $ZipFilePath -Force
}

Write-Host "Compressing output to $ZipFileName..." -ForegroundColor Yellow
try {
    Compress-Archive -Path "$SourceDir\*" -DestinationPath $ZipFilePath -ErrorAction Stop
    Write-Host "Zip created successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to create zip archive! Error: $($_.Exception.Message)" -ForegroundColor Red
    Pop-Location
    Exit 1
}

# 4. Git Commit (tag will be auto-created by gh release create)
Write-Host "Checking git status..." -ForegroundColor Cyan
$GitStatus = git status --porcelain
if ($GitStatus) {
    Write-Host "Uncommitted changes found. Committing..." -ForegroundColor Yellow
    git add .
    git commit -m "chore: release version $TAG_NAME"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Git commit failed!" -ForegroundColor Red
        Pop-Location
        Exit 1
    }
} else {
    Write-Host "No changes to commit." -ForegroundColor DarkGray
}

Write-Host "Pushing commits to origin..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Git push failed!" -ForegroundColor Red
    Pop-Location
    Exit 1
}

# 5. GitHub Release (gh release create auto-creates tag and pushes)
Write-Host "Checking if gh cli is installed..." -ForegroundColor Cyan
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "Creating GitHub Release $TAG_NAME..." -ForegroundColor Yellow

    # Modify your release notes here directly:
    $ReleaseNotes = @"
## $TAG_NAME ($(Get-Date -Format 'yyyy-MM-dd'))
app template

### New Feature
- 1 

### Optimize
- 1 optimize code structure

### Fix
- 1 fix some bug
"@

    gh release create $TAG_NAME $ZipFilePath `
        --title "Release $TAG_NAME" `
        --notes "$ReleaseNotes"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Release created successfully and artifact uploaded!" -ForegroundColor Green
    } else {
        Write-Host "Failed to create GitHub release." -ForegroundColor Red
        Pop-Location
        Exit 1
    }
} else {
    Write-Host "GitHub CLI (gh) is not installed. Skipping release creation." -ForegroundColor Red
    Pop-Location
    Exit 1
}

Write-Host "All tasks completed!" -ForegroundColor Green
Pop-Location
