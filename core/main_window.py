# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

import sys
import os
import json
from pathlib import Path

from gui.qt_core import *
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

        self.app_name = app_name
        self.logo_path = logo_path
        self.setWindowTitle(self.app_name)

        if logo_path and Path(logo_path).exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.user_manager = user_manager
        self.config_manager = ConfigManager()
        self.page_manager = PageManager(parent=self)
        
        # Load widgets from PyOneDark
        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)

        settings = Settings()
        self.settings = settings.items

        if self.user_manager:
            self.page_manager.set_user_manager(self.user_manager)

        self.dragPos = QPoint()
        self.background_cache = None
        self.last_window_size = QSize()
        self.splash_screen = None

        self.pages = {}
        self.nav_items = {}

        self.hide_grips = True

        self.background_cache = None
        self.last_window_size = QSize()

        if self.settings["custom_title_bar"]:
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.left_grip = PyGrips(self, "left", self.hide_grips)
            self.right_grip = PyGrips(self, "right", self.hide_grips)
            self.top_grip = PyGrips(self, "top", self.hide_grips)
            self.bottom_grip = PyGrips(self, "bottom", self.hide_grips)
            self.top_left_grip = PyGrips(self, "top_left", self.hide_grips)
            self.top_right_grip = PyGrips(self, "top_right", self.hide_grips)
            self.bottom_left_grip = PyGrips(self, "bottom_left", self.hide_grips)
            self.bottom_right_grip = PyGrips(self, "bottom_right", self.hide_grips)

        self.ui.left_menu.clicked.connect(self.btn_clicked)
        self.ui.left_menu.released.connect(self.btn_released)
        self.ui.title_bar.clicked.connect(self.btn_clicked)
        self.ui.title_bar.released.connect(self.btn_released)
        self.ui.left_column.clicked.connect(self.btn_clicked)
        self.ui.left_column.released.connect(self.btn_released)

        if self.settings["custom_title_bar"]:
            self.ui.title_bar.set_title(self.app_name)
        else:
            self.ui.title_bar.set_title(self.app_name)

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
        if not self.splash_screen:
            self.show()

        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        while self.ui.load_pages.pages.count() > 0:
            widget = self.ui.load_pages.pages.widget(0)
            self.ui.load_pages.pages.removeWidget(widget)
            widget.deleteLater()

        self.setup_navigation()

        self.settings_page = SettingsPage(self.config_manager, self)
        self.settings_page.background_changed.connect(self.on_background_changed)

        layout = self.ui.right_column.menu_1.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            layout.addWidget(self.settings_page)

        title_bar_menus = [
            {
                "btn_icon": "icon_settings.svg",
                "btn_id": "btn_top_settings",
                "btn_tooltip": "Settings",
                "is_active": False
            }
        ]
        self.ui.title_bar.add_menus(title_bar_menus)

        self.apply_global_font()

        visible_pages = self.page_manager.get_visible_pages()
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)
        if sorted_pages:
            first_page_id = sorted_pages[0][0]
            page_info = self.page_manager.get_page_info(first_page_id)
            if page_info:
                page_instance = page_info.create_instance(self)
                self.ui.load_pages.pages.addWidget(page_instance)
                self.pages[first_page_id] = page_instance
                MainFunctions.set_page(self, self.pages[first_page_id])
                self.ui.left_menu.select_only_one(f"btn_{first_page_id}")

    def toggle_settings_menu(self):
        """Toggle the right column for settings"""
        MainFunctions.set_right_column_menu(self, self.ui.right_column.menu_1)
        MainFunctions.toggle_right_column(self)

    def theme_changed(self):
        """Handle theme change signal"""
        Settings().refresh()
        Themes().refresh()
        self.settings = Settings().items
        self.ui.themes = Themes().items
        self.themes = self.ui.themes

        theme_name = "light" if "bright" in self.settings["theme_name"] else "dark"

        self.ui.left_menu.update_colors(
            dark_one = self.themes["app_color"]["dark_one"],
            dark_three = self.themes["app_color"]["dark_three"],
            dark_four = self.themes["app_color"]["dark_four"],
            bg_one = self.themes["app_color"]["bg_one"],
            icon_color = self.themes["app_color"]["icon_color"],
            icon_color_hover = self.themes["app_color"]["icon_hover"],
            icon_color_pressed = self.themes["app_color"]["icon_pressed"],
            icon_color_active = self.themes["app_color"]["icon_active"],
            context_color = self.themes["app_color"]["context_color"],
            text_foreground = self.themes["app_color"]["text_foreground"],
            text_active = self.themes["app_color"]["text_active"]
        )

        self.ui.left_menu.clear_menus()

        title_bar_menus = [
            {
                "btn_icon": "icon_settings.svg",
                "btn_id": "btn_top_settings",
                "btn_tooltip": "Settings",
                "is_active": False
            }
        ]
        self.ui.title_bar.clear_menus()
        self.ui.title_bar.add_menus(title_bar_menus)

        self.ui.window.set_stylesheet(
            bg_color=self.themes["app_color"]["bg_one"],
            border_color=self.themes["app_color"]["bg_two"],
            text_color=self.themes["app_color"]["text_foreground"]
        )

        self.ui.content_area_right_bg_frame.setStyleSheet(f'''
        #content_area_right_bg_frame {{
            border-radius: 8px;
            background-color: {self.themes["app_color"]["bg_two"]};
        }}
        ''')

        self.ui.left_column_frame.setStyleSheet(f"background: {self.themes['app_color']['bg_two']}")
        self.ui.left_menu_frame.setStyleSheet("")
        self.ui.title_bar.bg.setStyleSheet(f"background-color: {self.themes['app_color']['bg_two']}; border-radius: 8px;")

        from gui.widgets.py_title_bar.py_title_button import PyTitleButton
        from gui.core.functions import Functions

        self.ui.title_bar._dark_one = self.themes["app_color"]["dark_one"]
        self.ui.title_bar._bg_color = self.themes["app_color"]["bg_two"]
        self.ui.title_bar._div_color = self.themes["app_color"]["dark_four"]
        self.ui.title_bar._btn_bg_color = self.themes["app_color"]["bg_two"]
        self.ui.title_bar._btn_bg_color_hover = self.themes["app_color"]["bg_three"]
        self.ui.title_bar._btn_bg_color_pressed = self.themes["app_color"]["dark_one"]
        self.ui.title_bar._icon_color = self.themes["app_color"]["icon_color"]
        self.ui.title_bar._icon_color_hover = self.themes["app_color"]["icon_hover"]
        self.ui.title_bar._icon_color_pressed = self.themes["app_color"]["icon_pressed"]
        self.ui.title_bar._icon_color_active = self.themes["app_color"]["icon_active"]
        self.ui.title_bar._context_color = self.themes["app_color"]["context_color"]
        self.ui.title_bar._text_foreground = self.themes["app_color"]["text_foreground"]

        if hasattr(self.ui.title_bar, 'minimize_button'):
            self.ui.title_bar.bg_layout.removeWidget(self.ui.title_bar.minimize_button)
            self.ui.title_bar.minimize_button.deleteLater()
        if hasattr(self.ui.title_bar, 'maximize_restore_button'):
            self.ui.title_bar.bg_layout.removeWidget(self.ui.title_bar.maximize_restore_button)
            self.ui.title_bar.maximize_restore_button.deleteLater()
        if hasattr(self.ui.title_bar, 'close_button'):
            self.ui.title_bar.bg_layout.removeWidget(self.ui.title_bar.close_button)
            self.ui.title_bar.close_button.deleteLater()

        self.ui.title_bar.minimize_button = PyTitleButton(
            self, self.ui.central_widget, tooltip_text="Minimize app",
            dark_one=self.ui.title_bar._dark_one,
            bg_color=self.ui.title_bar._btn_bg_color,
            bg_color_hover=self.ui.title_bar._btn_bg_color_hover,
            bg_color_pressed=self.ui.title_bar._btn_bg_color_pressed,
            icon_color=self.ui.title_bar._icon_color,
            icon_color_hover=self.ui.title_bar._icon_color_hover,
            icon_color_pressed=self.ui.title_bar._icon_color_pressed,
            icon_color_active=self.ui.title_bar._icon_color_active,
            context_color=self.ui.title_bar._context_color,
            text_foreground=self.ui.title_bar._text_foreground,
            radius=6, icon_path=Functions.set_svg_icon("icon_minimize.svg")
        )
        self.ui.title_bar.minimize_button.released.connect(lambda: self.showMinimized())

        self.ui.title_bar.maximize_restore_button = PyTitleButton(
            self, self.ui.central_widget, tooltip_text="Maximize app",
            dark_one=self.ui.title_bar._dark_one,
            bg_color=self.ui.title_bar._btn_bg_color,
            bg_color_hover=self.ui.title_bar._btn_bg_color_hover,
            bg_color_pressed=self.ui.title_bar._btn_bg_color_pressed,
            icon_color=self.ui.title_bar._icon_color,
            icon_color_hover=self.ui.title_bar._icon_color_hover,
            icon_color_pressed=self.ui.title_bar._icon_color_pressed,
            icon_color_active=self.ui.title_bar._icon_color_active,
            context_color=self.ui.title_bar._context_color,
            text_foreground=self.ui.title_bar._text_foreground,
            radius=6, icon_path=Functions.set_svg_icon("icon_maximize.svg")
        )
        self.ui.title_bar.maximize_restore_button.released.connect(lambda: self.ui.title_bar.maximize_restore())

        self.ui.title_bar.close_button = PyTitleButton(
            self, self.ui.central_widget, tooltip_text="Close app",
            dark_one=self.ui.title_bar._dark_one,
            bg_color=self.ui.title_bar._btn_bg_color,
            bg_color_hover=self.ui.title_bar._btn_bg_color_hover,
            bg_color_pressed=self.ui.title_bar._context_color,
            icon_color=self.ui.title_bar._icon_color,
            icon_color_hover=self.ui.title_bar._icon_color_hover,
            icon_color_pressed=self.ui.title_bar._icon_color_active,
            icon_color_active=self.ui.title_bar._icon_color_active,
            context_color=self.ui.title_bar._context_color,
            text_foreground=self.ui.title_bar._text_foreground,
            radius=6, icon_path=Functions.set_svg_icon("icon_close.svg")
        )
        self.ui.title_bar.close_button.released.connect(lambda: self.close())

        if self.ui.title_bar._is_custom_title_bar:
            self.ui.title_bar.bg_layout.addWidget(self.ui.title_bar.minimize_button)
            self.ui.title_bar.bg_layout.addWidget(self.ui.title_bar.maximize_restore_button)
            self.ui.title_bar.bg_layout.addWidget(self.ui.title_bar.close_button)

        if self.isMaximized():
            self.ui.title_bar.maximize_restore_button.set_icon(Functions.set_svg_icon("icon_restore.svg"))

        title_bar_menus = [
            {
                "btn_icon": "icon_settings.svg",
                "btn_id": "btn_top_settings",
                "btn_tooltip": "Settings",
                "is_active": False
            }
        ]
        self.ui.title_bar.clear_menus()
        self.ui.title_bar.add_menus(title_bar_menus)

        self.setup_navigation()

        current_widget = self.ui.load_pages.pages.currentWidget()
        if current_widget and hasattr(current_widget, 'page_id'):
            self.ui.left_menu.select_only_one(f"btn_{current_widget.page_id}")

        if hasattr(self, 'settings_page'):
            self.settings_page.setStyleSheet("")
            if hasattr(self.settings_page, 'apply_base_style'):
                self.settings_page.apply_base_style(theme_name)
            for widget in self.settings_page.findChildren(QWidget):
                widget.setStyleSheet("")
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            self.settings_page.style().unpolish(self.settings_page)
            self.settings_page.style().polish(self.settings_page)
            self.settings_page.update()

        for page_id, page_instance in self.pages.items():
            if hasattr(page_instance, 'apply_base_style'):
                page_instance.apply_base_style(theme_name)

    def setup_navigation(self):
        """Setup navigation bar with registered pages"""
        visible_pages = self.page_manager.get_visible_pages()
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)

        left_menus = []

        for page_id, page_info in sorted_pages:
            if page_info.enabled and page_info.visible:
                icon_name = "icon_widgets.svg"
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

        self.ui.left_menu.add_menus(left_menus)

    def btn_clicked(self):
        btn = SetupMainWindow.setup_btns(self)
        if not btn: return

        btn_id = btn.objectName()

        if btn_id == "btn_top_settings":
            self.toggle_settings_menu()

        elif btn_id.startswith("btn_"):
            page_id = btn_id[4:]

            if page_id not in self.pages:
                page_info = self.page_manager.get_page_info(page_id)
                if page_info:
                    page_instance = page_info.create_instance(self)
                    self.ui.load_pages.pages.addWidget(page_instance)
                    self.pages[page_id] = page_instance

            if page_id in self.pages:
                self.ui.left_menu.select_only_one(btn_id)
                MainFunctions.set_page(self, self.pages[page_id])

    def btn_released(self):
        pass

    def resizeEvent(self, event):
        SetupMainWindow.resize_grips(self)

    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()

    def on_background_changed(self, bg_path):
        self.background_cache = None
        self.update()

    def paintEvent(self, event):
        background_config = self.config_manager.get_background_config()
        if background_config.get('enabled', False):
            if not self.background_cache or abs(self.width() - self.last_window_size.width()) > 10 or abs(self.height() - self.last_window_size.height()) > 10:
                self._update_background_cache(background_config)

            if self.background_cache:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing, False)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

                theme = Themes().items
                painter.fillRect(self.rect(), QColor(theme['app_color']['bg_one']))

                painter.setOpacity(background_config.get('opacity', 1.0))
                painter.drawPixmap(0, 0, self.background_cache)

                painter.end()

                self.ui.window.setStyleSheet("#pod_bg_app { background-color: transparent; border: none; }")
                self.ui.central_widget.setStyleSheet("background: transparent;")
        else:
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

    def apply_global_font(self):
        """Apply global font to all pages and widgets"""
        if not self.config_manager:
            return

        font_family = self.config_manager.get_font_family()
        font_size = self.config_manager.get_font_size()
        font = QFont(font_family, font_size)

        self.setFont(font)

        for page_instance in self.pages.values():
            if hasattr(page_instance, 'apply_global_font'):
                page_instance.apply_global_font()
            else:
                page_instance.setFont(font)
                for child in page_instance.findChildren(QWidget):
                    child.setFont(font)

    def closeEvent(self, event):
        self.config_manager.save_config()
        super().closeEvent(event)