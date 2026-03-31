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
            self.update_finished.emit(False, str(e))

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
            # Create a simple python script to handle file replacement
            updater_script = """
import os
import sys
import shutil
import time
import subprocess

def apply_update(src, dst, exe_name):
    print(f"Waiting for {exe_name} to close...")
    time.sleep(2)
    
    try:
        # If running as standalone dist, src might contain a subfolder like 'main.dist'
        # We need to find the actual content folder
        content_src = src
        for item in os.listdir(src):
            if os.path.isdir(os.path.join(src, item)) and item.endswith('.dist'):
                content_src = os.path.join(src, item)
                break
        
        print(f"Copying from {content_src} to {dst}...")
        # Copy all files from content_src to dst
        for item in os.listdir(content_src):
            s = os.path.join(content_src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        
        print("Update applied. Restarting application...")
        app_exe = os.path.join(dst, exe_name)
        if not app_exe.endswith('.exe'): app_exe += '.exe'
        
        subprocess.Popen([app_exe])
        
        # Cleanup temp
        time.sleep(1)
        shutil.rmtree(os.path.dirname(src))
    except Exception as e:
        print(f"Update failed: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    apply_update(sys.argv[1], sys.argv[2], sys.argv[3])
"""
            temp_dir = Path("temp_update")
            temp_dir.mkdir(exist_ok=True)
            updater_file = temp_dir / "apply_update.py"
            with open(updater_file, "w", encoding="utf-8") as f:
                f.write(updater_script)
            
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
            
            # If we're running as a python script, we shouldn't start python.exe in our dir
            if exe_path.endswith('.py') or exe_name.lower() == 'python.exe':
                restart_cmd = f'start "" "{sys.executable}" "{os.path.join(app_root_win, exe_name)}"'
            else:
                restart_cmd = f'start "" "{os.path.join(app_root_win, exe_name)}"'
            
            bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
echo Updating application...
xcopy /s /e /y "{extracted_path_win}\\*" "{app_root_win}\\"
echo Update complete. Restarting...
{restart_cmd}
del "%~f0"
"""
            bat_file = temp_dir / "finish_update.bat"
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write(bat_content)
            
            # Launch bat and exit app
            subprocess.Popen([str(bat_file)], shell=True)
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
