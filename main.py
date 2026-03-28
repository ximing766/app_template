import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.main_window import MainWindow
from user_mag import UserManager, LoginController
from database.database_manager import DatabaseManager
from pages.serial_dashboard_page import SerialDashboardPage
from core.simple_logger import SimpleLogger

APP_NAME = "APP Template"
APP_VERSION = "1.0.0"
GITHUB_REPO = "https://github.com/ximing766/app_template"  # Replace with your actual GitHub repo

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    db_manager = DatabaseManager()
    user_manager = UserManager()
    
    # Initialize and show login dialog
    # login_controller = LoginController(user_manager)
    # if not login_controller.show_login_dialog():
    #     sys.exit(0)
    
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
    main_window = MainWindow(
        app_name=APP_NAME,
        logo_path=logo_path,
        user_manager=user_manager
    )
    
    main_window.page_manager.register_page(
        "serial", "Serial", SerialDashboardPage,
        icon="icon_restore.svg", tooltip="Serial", order=10
    )
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()