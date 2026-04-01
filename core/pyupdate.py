# -*- coding: utf-8 -*-

import os
import sys
import json
import zipfile
import shutil
import subprocess
import time
from pathlib import Path
from PySide6.QtCore import QThread, Signal
import requests

class UpdateManager(QThread):
    """Manages the application update process"""
    status_changed = Signal(str)
    progress_changed = Signal(int)
    update_finished = Signal(bool, str)

    def __init__(self, repo_path, current_version):
        super().__init__()
        self.repo_path = repo_path
        self.current_version = current_version
        self.update_data = None
        self.mode = "check" # check, download, apply

    def set_mode(self, mode, update_data=None):
        self.mode = mode
        if update_data:
            self.update_data = update_data

    def run(self):
        if self.mode == "check":
            self.check_for_updates()
        elif self.mode == "download":
            self.download_update()
        elif self.mode == "apply":
            # In apply mode, update_data stores the path to the extracted files
            self.apply_update(self.update_data)

    def check_for_updates(self):
        """Check for latest release on GitHub"""
        self.status_changed.emit("Checking for updates...")
        try:
            url = f"https://api.github.com/repos/{self.repo_path}/releases/latest"
            print(f"\n[UpdateManager] Checking URL: {url}")
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('tag_name', '').lstrip('v')
                
                has_update = self._compare_versions(latest_version, self.current_version)
                
                result = {
                    'has_update': has_update,
                    'latest_version': latest_version,
                    'release_notes': data.get('body', ''),
                    'download_url': self._get_asset_url(data),
                    'tag_name': data.get('tag_name', '')
                }
                self.update_data = result
                self.update_finished.emit(True, "Check completed")
            else:
                self.update_finished.emit(False, f"GitHub API error: {response.status_code}")
        except Exception as e:
            self.update_finished.emit(False, "Unknown error")

    def download_update(self):
        """Download the update package"""
        if not self.update_data or not self.update_data.get('download_url'):
            self.update_finished.emit(False, "No download URL available")
            return

        url = self.update_data['download_url']
        self.status_changed.emit("Downloading update...")
        
        try:
            temp_dir = Path("temp_update")
            temp_dir.mkdir(exist_ok=True)
            zip_path = temp_dir / "update.zip"

            response = requests.get(url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_changed.emit(progress)
            
            self.status_changed.emit("Extracting update...")
            extract_path = temp_dir / "extracted"
            if extract_path.exists():
                shutil.rmtree(extract_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            self.update_finished.emit(True, str(extract_path))
        except Exception as e:
            self.update_finished.emit(False, str(e))

    def apply_update(self, extracted_path):
        """Prepare and launch the updater script"""
        self.status_changed.emit("Preparing update...")
        try:
            app_root = os.path.abspath(os.getcwd())
            # Determine correct executable path to restart
            if getattr(sys, 'frozen', False):
                # PyInstaller
                exe_path = sys.executable
            elif '__compiled__' in globals():
                # Nuitka
                exe_path = sys.argv[0]
            else:
                # Normal python script
                exe_path = sys.argv[0]
                
            exe_name = os.path.basename(exe_path)
            
            # Use backslashes for Windows xcopy
            extracted_path_win = str(Path(extracted_path).resolve())
            app_root_win = str(Path(app_root).resolve())
            temp_update_win = str(Path(extracted_path).parent.resolve())
            
            # If we're running as a python script, we shouldn't start python.exe in our dir
            if exe_path.endswith('.py') or exe_name.lower() == 'python.exe':
                restart_cmd = f'start "" "{sys.executable}" "{os.path.join(app_root_win, exe_name)}"'
            else:
                restart_cmd = f'start "" "{os.path.join(app_root_win, exe_name)}"'
            
            # Create a batch file in system TEMP to avoid locking temp_update folder
            temp_bat_dir = os.environ.get('TEMP', app_root)
            bat_file = os.path.join(temp_bat_dir, "finish_app_update.bat")
            
            bat_content = f"""@echo off
title App Update
echo Updating application... Please wait.

:: Give the parent application a moment to close normally
timeout /t 2 /nobreak > nul

:: Force kill the application if it's still running to release file locks
taskkill /f /im "{exe_name}" > nul 2>&1

:: Wait a bit more to ensure file locks are released by the OS
timeout /t 1 /nobreak > nul

:: Ensure we copy from the right source (handle potential main.dist subfolder)
set "src={extracted_path_win}"
if exist "%src%\\main.dist" set "src=%src%\\main.dist"

echo Copying files from "%src%" to "{app_root_win}"...
xcopy /s /e /y /q /r /h /k "%src%\\*" "{app_root_win}\\"

if errorlevel 1 (
    echo.
    echo [ERROR] Copy failed! Update might be incomplete.
    echo Please ensure the application is completely closed and try again.
    pause
) else (
    echo.
    echo [SUCCESS] Update applied. Cleaning up temporary files...
    rmdir /s /q "{temp_update_win}"
    echo Restarting application...
    {restart_cmd}
)
del "%~f0"
"""
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write(bat_content)
            
            # Launch bat and exit app in a new console window
            # Use CREATE_NEW_CONSOLE only, as DETACHED_PROCESS conflicts with it and causes WinError 87
            subprocess.Popen(
                ["cmd.exe", "/c", bat_file], 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            sys.exit(0)
            
        except Exception as e:
            self.update_finished.emit(False, str(e))

    def _compare_versions(self, v1, v2):
        try:
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            return v1_parts > v2_parts
        except:
            return v1 != v2

    def _get_asset_url(self, release_data):
        assets = release_data.get('assets', [])
        if not assets:
            return release_data.get('zipball_url') # Fallback to source zip
        
        # Prefer windows zip
        for asset in assets:
            name = asset.get('name', '').lower()
            if 'windows' in name and name.endswith('.zip'):
                return asset.get('browser_download_url')
        
        return assets[0].get('browser_download_url')
