# ==============================================================================
# PySide6 App Build and Release Script
# This script builds the application using Nuitka and releases it to GitHub
# ==============================================================================

# 1. Extract Version from main.py
$MainFile = "main.py"
$VersionRegex = 'APP_VERSION\s*=\s*"([^"]+)"'
$MainContent = Get-Content $MainFile -Raw
if ($MainContent -match $VersionRegex) {
    $APP_VERSION = $matches[1]
    Write-Host "Found version in $MainFile: v$APP_VERSION" -ForegroundColor Green
} else {
    Write-Host "Error: Could not find APP_VERSION in $MainFile" -ForegroundColor Red
    Exit 1
}

$APP_NAME = "PowerMeterBluetoothTest"
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

# 4. Git Commit and Tag
Write-Host "Checking git status..." -ForegroundColor Cyan
$GitStatus = git status --porcelain
if ($GitStatus) {
    Write-Host "Uncommitted changes found. Committing..." -ForegroundColor Yellow
    git add .
    git commit -m "chore: release version $TAG_NAME"
} else {
    Write-Host "No changes to commit." -ForegroundColor DarkGray
}

Write-Host "Creating tag $TAG_NAME..." -ForegroundColor Yellow
# Check if tag exists
$TagExists = git tag -l $TAG_NAME
if ($TagExists) {
    Write-Host "Tag $TAG_NAME already exists. Deleting local and remote tag..." -ForegroundColor DarkYellow
    git tag -d $TAG_NAME
    git push origin --delete $TAG_NAME
}
git tag -a $TAG_NAME -m "Release $TAG_NAME"

Write-Host "Pushing commits and tags to origin..." -ForegroundColor Yellow
git push origin main
git push origin $TAG_NAME

# 5. GitHub Release (requires gh cli)
Write-Host "Checking if gh cli is installed..." -ForegroundColor Cyan
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "Creating GitHub Release $TAG_NAME..." -ForegroundColor Yellow
    
    # Check if release exists, if so, delete it first
    $ReleaseExists = gh release view $TAG_NAME 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Release $TAG_NAME already exists. Deleting..." -ForegroundColor DarkYellow
        gh release delete $TAG_NAME -y
    }
    
    # Create release and upload zip file
    gh release create $TAG_NAME $ZipFilePath `
        --title "Release $TAG_NAME" `
        --notes "Automated release of version $TAG_NAME"
        
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
