import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.main_window import MainWindow
from user_mag import UserManager, LoginController, UserManagementPage
from database.database_manager import DatabaseManager
from pages.home_page import HomePage
from core.constants import APP_NAME, APP_VERSION

import warnings
warnings.filterwarnings("ignore")

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    db_manager = DatabaseManager()
    user_manager = UserManager()
    
    # Initialize and show login dialog
    login_controller = LoginController(user_manager)
    if not login_controller.show_login_dialog():
        sys.exit(0)
    
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
    main_window = MainWindow(
        app_name=APP_NAME,
        logo_path=logo_path,
        user_manager=user_manager
    )

    main_window.page_manager.register_page(
        "home", "Home", HomePage,
        icon="icon_home.svg", tooltip="Home", order=10
    )

    main_window.page_manager.register_page(
        "user_management", "Users", UserManagementPage,
        icon="icon_add_user.svg", tooltip="User Management", order=90,
        required_role="admin"
    )

    sys.exit(app.exec())

if __name__ == '__main__':
    main()