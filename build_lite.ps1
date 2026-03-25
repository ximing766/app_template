# Set Nuitka cache directory to a local folder to keep the system clean
$env:NUITKA_CACHE_DIR = "nuitka_cache"

Write-Host "Starting optimized build for PowerMeterBluetoothTest..." -ForegroundColor Cyan

# Check if output directory exists, if not create it
if (-not (Test-Path "output")) {
    New-Item -ItemType Directory -Path "output"
}

# Run Nuitka build
python -m nuitka `
    --standalone `
    --windows-console-mode=disable `
    --enable-plugin=pyqt6 `
    --include-qt-plugins=sensible,styles `
    --windows-icon-from-ico=assets/logo.ico `
    --include-data-dir=assets=assets `
    --include-data-dir=config=config `
    --include-data-dir=database=database `
    --output-dir=output `
    --output-filename=PowerMeterBluetoothTest `
    --assume-yes-for-downloads `
    --jobs=8 `
    --python-flag=-OO `
    --nofollow-import-to=numpy,scipy,pandas,matplotlib,IPython,PIL `
    --remove-output `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Check output in: output/PowerMeterBluetoothTest" -ForegroundColor Cyan
} else {
    Write-Host "Build failed!" -ForegroundColor Red
}
