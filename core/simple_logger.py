import os
import datetime
from pathlib import Path

class SimpleLogger:
    def __init__(self, log_dir="LOG"):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.log_dir = self.base_dir / log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
    
    def ensure_today_dir(self):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        date_dir = self.log_dir / date_str
        date_dir.mkdir(exist_ok=True)
        return date_dir

    def start_logging(self, prefix="serial"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.txt"
        date_dir = self.ensure_today_dir()
        self.current_log_file = date_dir / filename
        return str(self.current_log_file)

    def log(self, message):
        if self.current_log_file:
            try:
                with open(self.current_log_file, "a", encoding="utf-8") as f:
                    f.write(message)
            except Exception as e:
                print(f"Logging error: {e}")

    def get_log_dir(self):
        return str(self.log_dir)

    def get_current_log_file(self):
        return str(self.current_log_file) if self.current_log_file else None
