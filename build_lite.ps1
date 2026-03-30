# ==============================================================================
# PySide6 App Build and Release Script
# This script builds the application using Nuitka and releases it to GitHub
# ==============================================================================

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

# 1. Extract Version from core/constants.py
$ConstFile = "core/constants.py"
$VersionRegex = 'APP_VERSION\s*=\s*"([^"]+)"'
$ConstContent = Get-Content $ConstFile -Raw
if ($ConstContent -match $VersionRegex) {
    $APP_VERSION = $matches[1]
    Write-Host "Found version in ${ConstFile}: v$APP_VERSION" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find APP_VERSION in $ConstFile" -ForegroundColor Red
    Exit 1
}

$MainFile = "main.py"

$APP_NAME = "app demo"
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
# Added --lto=yes for Link Time Optimization (smaller size)
# Kept --nofollow-import-to to exclude heavy data science packages
Write-Host "Building executable with Nuitka..." -ForegroundColor Yellow
python -m nuitka `
    --standalone `
    --windows-console-mode=disable `
    --enable-plugin=pyqt6 `
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
    --lto=yes `
    --nofollow-import-to=numpy,scipy,pandas,matplotlib,IPython,PIL,tkinter `
    --remove-output `
    $MainFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed! Exiting." -ForegroundColor Red
    Exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green

# 3. Zip the output for Release
$ZipFileName = "$APP_NAME-$TAG_NAME-Windows.zip"
$ZipFilePath = "$OUTPUT_DIR\$ZipFileName"
$SourceDir = "$OUTPUT_DIR\$APP_NAME.dist"

if (Test-Path $ZipFilePath) {
    Remove-Item $ZipFilePath -Force
}

Write-Host "Compressing output to $ZipFileName..." -ForegroundColor Yellow
Compress-Archive -Path "$SourceDir\*" -DestinationPath $ZipFilePath

# 4. Git Commit (tag will be auto-created by gh release create)
Write-Host "Checking git status..." -ForegroundColor Cyan
$GitStatus = git status --porcelain
if ($GitStatus) {
    Write-Host "Uncommitted changes found. Committing..." -ForegroundColor Yellow
    git add .
    git commit -m "chore: release version $TAG_NAME"
} else {
    Write-Host "No changes to commit." -ForegroundColor DarkGray
}

Write-Host "Pushing commits to origin..." -ForegroundColor Yellow
git push origin main

# 5. GitHub Release (gh release create auto-creates tag and pushes)
Write-Host "Checking if gh cli is installed..." -ForegroundColor Cyan
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "Creating GitHub Release $TAG_NAME..." -ForegroundColor Yellow
    
    # Check if release exists, if so, delete it first
    $ReleaseExists = gh release view $TAG_NAME 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Release $TAG_NAME already exists. Deleting..." -ForegroundColor DarkYellow
        gh release delete $TAG_NAME -y
    }
    
    # Get Release Notes from a file if it exists, otherwise use a default
    $NotesFile = "RELEASE_NOTES.md"
    $ReleaseNotes = "Automated release of version $TAG_NAME`n`nBuilt on $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    if (Test-Path $NotesFile) {
        $ReleaseNotes = Get-Content $NotesFile -Raw
        Write-Host "Found release notes in $NotesFile" -ForegroundColor Cyan
    }
    
    # Create release and upload zip file
    gh release create $TAG_NAME $ZipFilePath `
        --title "Release $TAG_NAME" `
        --notes "$ReleaseNotes"
        
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Release created successfully and artifact uploaded!" -ForegroundColor Green
    } else {
        Write-Host "Failed to create GitHub release." -ForegroundColor Red
    }
} else {
    Write-Host "GitHub CLI (gh) is not installed. Skipping release creation." -ForegroundColor Red
    Write-Host "To enable auto-releases, install GitHub CLI: https://cli.github.com/" -ForegroundColor Yellow
}

Write-Host "All tasks completed!" -ForegroundColor Green
