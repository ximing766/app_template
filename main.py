import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import logger first for early initialization
from Log import logger, setup_logger

from core.main_window import MainWindow
from user_mag import UserManager, LoginController, UserManagementPage
from database.database_manager import DatabaseManager
from pages.home_page import HomePage
from pages.serial_page import SerialPage
from serial_comm.serial_manager import SerialManager
from core.constants import APP_NAME, APP_VERSION

import warnings
warnings.filterwarnings("ignore")


def _set_windows_app_id(app_id: str) -> None:
    """Give the process its own taskbar identity.

    Without this the taskbar button is grouped with python.exe and shows the
    interpreter's icon instead of the application's.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ctypes.c_wchar_p(app_id))
    except Exception:
        pass


def main():
    logger.info("=" * 60)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info("=" * 60)

    try:
        _set_windows_app_id(APP_NAME)

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # Release serial threads on shutdown (ports stay open throughout the session).
        app.aboutToQuit.connect(SerialManager.instance().close_all_ports)

        db_manager = DatabaseManager()

        user_manager = UserManager()

        # Initialize and show login dialog
        login_controller = LoginController(user_manager)
        if not login_controller.show_login_dialog():
            logger.info("User cancelled login, exiting application")
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
            "serial", "Serial", SerialPage,
            icon="icon_signal.svg", tooltip="Serial Port Management", order=20
        )

        main_window.page_manager.register_page(
            "user_management", "Users", UserManagementPage,
            icon="icon_add_user.svg", tooltip="User Management", order=90,
            required_role="admin"
        )

        logger.info("Application started successfully")
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")

        return exit_code

    except Exception as e:
        logger.warning(f"Fatal error during application startup: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())