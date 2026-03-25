#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QPointF
from qfluentwidgets import setTheme, Theme
from qfluentwidgets import FluentIcon as FIF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.main_window import MainWindow
from user_mag import UserManager, LoginController
from database.database_manager import DatabaseManager
from pages.serial_dashboard_page import SerialDashboardPage
from core.simple_logger import SimpleLogger

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    APP_NAME = "APP"
    APP_VERSION = "1.0.0"
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Your Organization")
    
    SimpleLogger().ensure_today_dir()
    
    user_manager = UserManager()
    if user_manager.is_user_management_enabled():
        login_controller = LoginController(user_manager)
        if not login_controller.show_login_dialog():
            sys.exit(0)
        
        if not login_controller.is_authenticated():
            QMessageBox.critical(None, "登录失败", "用户认证失败，应用程序将退出。")
            sys.exit(1)

    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
    if not os.path.exists(logo_path):
        logo_path = None
    
    window = MainWindow(
        app_name=APP_NAME,
        logo_path=logo_path,
        user_manager=user_manager
    )
    
    try:
        db_manager = DatabaseManager()
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    
    # window.page_manager.register_page(
    #     page_id="user_management",
    #     title="用户管理",
    #     page_class=UserManagementPage,
    #     icon=FIF.PEOPLE,
    #     tooltip="管理系统用户和权限",
    #     order=10,
    #     required_role="admin"  # XXX Only admin can access
    # )

    window.page_manager.register_page(
        page_id="serial_dashboard",
        title="串口调试",
        page_class=SerialDashboardPage,
        icon=FIF.CONNECT,
        tooltip="串口调试工具",
        order=30
    )
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
