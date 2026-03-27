# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

import sys
import os
import json
from pathlib import Path

from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.uis.windows.main_window.ui_main import UI_MainWindow
from gui.uis.windows.main_window.functions_main_window import MainFunctions
from gui.uis.windows.main_window.setup_main_window import SetupMainWindow
from gui.widgets import *

from config.config_manager import ConfigManager
from pages import SettingsPage, BasePage, PageManager
from .splash_screen import show_splash_screen

class MainWindow(QMainWindow):
    def __init__(self, app_name="Generic App", logo_path=None, user_manager=None):
        super().__init__()
        
        # Basic window setup
        self.app_name = app_name
        self.logo_path = logo_path
        self.setWindowTitle(self.app_name)

        if logo_path and Path(logo_path).exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
        # Load widgets from PyOneDark
        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)

        # LOAD SETTINGS
        settings = Settings()
        self.settings = settings.items

        # Initialize managers
        self.user_manager = user_manager
        self.config_manager = ConfigManager()
        self.page_manager = PageManager(parent=self)
        
        # Set user manager for page manager if available
        if hasattr(self, 'user_manager') and self.user_manager:
            self.page_manager.set_user_manager(self.user_manager)
        
        # Load user-specific config if user management is enabled
        if self.user_manager and self.user_manager.is_authenticated():
            current_user = self.user_manager.get_current_user()
            if current_user:
                self.config_manager.set_current_user(current_user['username'])
                user_config = self.user_manager.load_user_config(current_user['username'])
                if user_config:
                    self.config_manager.load_config_from_dict(user_config)
        
        # Window properties
        self.dragPos = QPoint()
        self.background_cache = None
        self.last_window_size = QSize()
        self.splash_screen = None
        
        # Page registry for dynamic page management
        self.pages = {}
        self.nav_items = {}
        
        self.hide_grips = True
        
        # Add background painting support
        self.background_cache = None
        self.last_window_size = QSize()
        
        # Remove default title bar if setting allows
        if self.settings["custom_title_bar"]:
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            # Add grips
            self.left_grip = PyGrips(self, "left", self.hide_grips)
            self.right_grip = PyGrips(self, "right", self.hide_grips)
            self.top_grip = PyGrips(self, "top", self.hide_grips)
            self.bottom_grip = PyGrips(self, "bottom", self.hide_grips)
            self.top_left_grip = PyGrips(self, "top_left", self.hide_grips)
            self.top_right_grip = PyGrips(self, "top_right", self.hide_grips)
            self.bottom_left_grip = PyGrips(self, "bottom_left", self.hide_grips)
            self.bottom_right_grip = PyGrips(self, "bottom_right", self.hide_grips)

        # Set Signals
        self.ui.left_menu.clicked.connect(self.btn_clicked)
        self.ui.left_menu.released.connect(self.btn_released)
        self.ui.title_bar.clicked.connect(self.btn_clicked)
        self.ui.title_bar.released.connect(self.btn_released)
        self.ui.left_column.clicked.connect(self.btn_clicked)
        self.ui.left_column.released.connect(self.btn_released)

        # Add Title
        if self.settings["custom_title_bar"]:
            self.ui.title_bar.set_title(self.app_name)
        else:
            self.ui.title_bar.set_title(self.app_name)

        self.show_splash_screen()
        QTimer.singleShot(100, self.init_ui)
        
    def show_splash_screen(self):
        """Show splash screen during initialization"""
        self.splash_screen = show_splash_screen(self.app_name, self.logo_path, duration=2000)
        self.splash_screen.finished.connect(self.on_splash_finished)
    
    def on_splash_finished(self):
        """Called when splash screen finishes"""
        if self.splash_screen:
            self.splash_screen.deleteLater()
            self.splash_screen = None
        self.show()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Clear original pages in stacked widget
        while self.ui.load_pages.pages.count() > 0:
            widget = self.ui.load_pages.pages.widget(0)
            self.ui.load_pages.pages.removeWidget(widget)
            widget.deleteLater()

        self.setup_navigation()
        
        # Setup settings widget in right column
        self.settings_page = SettingsPage(self.config_manager, self)
        self.settings_page.background_changed.connect(self.on_background_changed)

        # Pass user_manager to settings page if available
        if hasattr(self, 'user_manager') and self.user_manager:
            self.settings_page.user_manager = self.user_manager
            
            self.user_manager.user_logged_in.connect(self.on_user_login_changed)
            self.user_manager.user_logged_out.connect(self.on_user_login_changed)
        
        # Clear existing layout and add settings page
        layout = self.ui.right_column.menu_1.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            layout.addWidget(self.settings_page)
            
        # Add Title bar menus (like Settings button)
        title_bar_menus = [
            {
                "btn_icon": "icon_settings.svg",
                "btn_id": "btn_top_settings",
                "btn_tooltip": "Settings",
                "is_active": False
            }
        ]
        self.ui.title_bar.add_menus(title_bar_menus)
        
        # Set initial page
        visible_pages = self.page_manager.get_visible_pages()
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)
        if sorted_pages:
            first_page_id = sorted_pages[0][0]
            if first_page_id in self.pages:
                MainFunctions.set_page(self, self.pages[first_page_id])
                self.ui.left_menu.select_only_one(f"btn_{first_page_id}")
    
    def toggle_settings_menu(self):
        """Toggle the right column for settings"""
        MainFunctions.set_right_column_menu(self, self.ui.right_column.menu_1)
        MainFunctions.toggle_right_column(self)
    
    def theme_changed(self):
        """Handle theme change signal"""
        MainFunctions.theme_changed(self)
    
    def setup_navigation(self):
        """Setup navigation bar with registered pages"""
        visible_pages = self.page_manager.get_visible_pages()
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)
        
        left_menus = []
        
        for page_id, page_info in sorted_pages:
            if page_info.enabled and page_info.visible:
                page_instance = page_info.create_instance(self)
                
                # Add page to Stacked Widget
                self.ui.load_pages.pages.addWidget(page_instance)
                self.pages[page_id] = page_instance
                
                # Determine icon
                icon_name = "icon_widgets.svg" # Default
                if page_id == "serial_dashboard": icon_name = "icon_restore.svg"
                elif page_id == "user_management": icon_name = "icon_add_user.svg"

                is_top = page_info.order < 90

                menu_item = {
                    "btn_icon" : icon_name,
                    "btn_id" : f"btn_{page_id}",
                    "btn_text" : page_info.title,
                    "btn_tooltip" : page_info.tooltip,
                    "show_top" : is_top,
                    "is_active" : False
                }
                left_menus.append(menu_item)
                
        # Add menus to PyOneDark left menu
        self.ui.left_menu.add_menus(left_menus)

    def btn_clicked(self):
        btn = SetupMainWindow.setup_btns(self)
        if not btn: return
        
        btn_id = btn.objectName()

        # Handle top settings
        if btn_id == "btn_top_settings":
            self.toggle_settings_menu()

        # Handle page navigation
        elif btn_id.startswith("btn_") and btn_id[4:] in self.pages:
            page_id = btn_id[4:]
            self.ui.left_menu.select_only_one(btn_id)
            MainFunctions.set_page(self, self.pages[page_id])

    def btn_released(self):
        pass

    def resizeEvent(self, event):
        SetupMainWindow.resize_grips(self)

    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()

    def on_user_login_changed(self): 
        if self.user_manager and self.user_manager.is_logged_in():
            current_user = self.user_manager.get_current_user()
            if current_user:
                self.config_manager.set_current_user(current_user['username'])
                user_config = self.user_manager.load_user_config(current_user['username'])
                if user_config:
                    self.config_manager.load_config_from_dict(user_config)
        else:
            self.config_manager.set_current_user(None)
            self.config_manager.reload_config()
        
        if hasattr(self, 'page_manager'):
            self.page_manager.refresh_page_permissions()
    
    def on_background_changed(self, bg_path):
        self.background_cache = None
        self.update()

    def paintEvent(self, event):
        background_config = self.config_manager.get_background_config()
        if background_config.get('enabled', False):
            if not self.background_cache or self.size() != self.last_window_size:
                self._update_background_cache(background_config)
            
            if self.background_cache:
                painter = QPainter(self)
                
                # Fill with default background color first to avoid transparent holes
                theme = Themes().items
                painter.fillRect(self.rect(), QColor(theme['app_color']['bg_one']))
                
                painter.setOpacity(background_config.get('opacity', 1.0))
                painter.drawPixmap(0, 0, self.width(), self.height(), self.background_cache)
                
                # Make the app background transparent so we can see the window background
                self.ui.window.setStyleSheet("#pod_bg_app { background-color: transparent; border: none; }")
                self.ui.central_widget.setStyleSheet("background: transparent;")
        else:
            # Restore default style if background is disabled
            theme = Themes().items
            self.ui.window.setStyleSheet(f"#pod_bg_app {{ background-color: {theme['app_color']['bg_one']}; border: 2px solid {theme['app_color']['bg_two']}; }}")
        
        super().paintEvent(event)

    def _update_background_cache(self, background_config):
        current_image = background_config.get('current_image')
        if not current_image:
            return
        
        background_path = Path(current_image)
        if not background_path.is_absolute():
            app_dir = Path(__file__).parent.parent
            background_path = app_dir / current_image
            
        if background_path.exists():
            size = self.size()
            background = QPixmap(str(background_path))
            if not background.isNull():
                self.background_cache = background.scaled(
                    size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.last_window_size = size

    def closeEvent(self, event):
        self.config_manager.save_config()
        super().closeEvent(event)