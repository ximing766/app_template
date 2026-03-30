# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

import os
import json
import urllib.request
from PySide6.QtCore import Qt, Signal, QUrl, QThread
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel, QScrollArea, QFrame, QMessageBox, QPushButton, QComboBox
from PySide6.QtGui import QDesktopServices
from .base_page import BasePage
from core.constants import APP_VERSION, GITHUB_REPO

class UpdateCheckerThread(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, repo_path, current_version):
        super().__init__()
        self.repo_path = repo_path
        self.current_version = current_version

    def run(self):
        try:
            # Format: ximing766/app_template
            url = f"https://api.github.com/repos/{self.repo_path}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data.get('tag_name', '').lstrip('v')
                release_notes = data.get('body', 'No release notes provided.')
                download_url = data.get('html_url', '')
                
                # Check if there are assets attached
                assets = data.get('assets', [])
                if assets:
                    download_url = assets[0].get('browser_download_url', download_url)

                self.result_ready.emit({
                    'latest_version': latest_version,
                    'release_notes': release_notes,
                    'download_url': download_url,
                    'has_update': self._compare_versions(latest_version, self.current_version)
                })
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _compare_versions(self, v1, v2):
        """Return True if v1 is newer than v2"""
        try:
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            return v1_parts > v2_parts
        except:
            return v1 != v2

class PushSettingCard(QFrame):
    clicked = Signal()
    
    def __init__(self, button_text, title="", description="", parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.button = QPushButton(button_text)
        self.button.setMinimumHeight(40)
        self.button.clicked.connect(self.clicked.emit)
        self.main_layout.addWidget(self.button)
        
    def setContent(self, text):
        self.button.setText(text)

class HyperlinkCard(QFrame):
    def __init__(self, url, button_text, title="", description="", parent=None):
        super().__init__(parent)
        self.url = url
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.button = QPushButton(button_text)
        self.button.setMinimumHeight(40)
        self.button.clicked.connect(self.open_url)
        self.main_layout.addWidget(self.button)
        
    def open_url(self):
        QDesktopServices.openUrl(QUrl(self.url))

class ComboSettingCard(QFrame):
    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.combo = QComboBox()
        self.combo.setMinimumHeight(40)
        
        # Center text without making it truly editable by user
        # We use a readonly lineedit which is the most reliable way to center text in QComboBox
        self.combo.setEditable(True)
        self.combo.lineEdit().setReadOnly(True)
        self.combo.lineEdit().setAlignment(Qt.AlignCenter)
        
        # Style to match other buttons and hide the edit cursor
        self.combo.lineEdit().setStyleSheet("background: transparent; border: none; selection-background-color: transparent;")
        
        if items:
            self.combo.addItems(items)
            
        self.main_layout.addWidget(self.combo)

class SettingsPage(BasePage):
    """Settings page with theme management and other general settings"""
    background_changed = Signal(str) 

    def __init__(self, config_manager=None, parent=None):
        self.config_manager = config_manager
        self.user_manager = None
        super().__init__("settings", parent)
    
    def init_content(self):
        """Initialize page content"""
        scroll_widget = QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_widget.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QWidget#scroll_content { background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scroll_content")
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(10)  
        content_layout.setContentsMargins(10, 10, 10, 10)  
        
        # Appearance
        current_theme_display = "Dark"
        current_theme_name = "dark"
        if self.config_manager:
            current_theme_name = self.config_manager.get_theme()
            current_theme_display = "Light" if current_theme_name == "light" else "Dark"
        else:
            # Fall back to PyDracula settings if no config manager
            try:
                from gui.core.json_settings import Settings
                settings = Settings()
                if "bright" in settings.items.get("theme_name", ""):
                    current_theme_display = "Light"
            except:
                pass
        
        self.theme_card = PushSettingCard(current_theme_display)
        self.theme_card.clicked.connect(self.on_theme_clicked)
        
        self.background_card = PushSettingCard("BACKGROUND")
        self.background_card.clicked.connect(self.cycle_background_image)
        
        # Font selection card with unified style and centered text
        fonts = [
            "Consolas",
            "Courier New",
            "Lucida Console",
            "JetBrains Mono",
            "Cascadia Code"
        ]
        self.font_card = ComboSettingCard(fonts)
        self.font_combo = self.font_card.combo
        
        current_font_family = "Courier New"
        if self.config_manager:
            current_font_family = self.config_manager.get_font_family()
        index = self.font_combo.findText(current_font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        
        # Opacity slider
        opacity_container = QFrame()
        opacity_container.setStyleSheet("background-color: transparent; border: none;")
        opacity_layout = QHBoxLayout(opacity_container)
        opacity_layout.setContentsMargins(0, 10, 0, 10)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        current_opacity = 100
        if self.config_manager:
            current_opacity = int(self.config_manager.get_background_opacity() * 100)
        self.opacity_slider.setValue(current_opacity)
        self.opacity_value_label = QLabel(f"{current_opacity}%")
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value_label)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        # Font size slider
        font_size_container = QFrame()
        font_size_container.setStyleSheet("background-color: transparent; border: none;")
        font_size_layout = QHBoxLayout(font_size_container)
        font_size_layout.setContentsMargins(0, 10, 0, 10)
        
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(6, 32)
        current_font_size = 10
        if self.config_manager:
            current_font_size = self.config_manager.get_font_size()
        self.font_size_slider.setValue(current_font_size)
        self.font_size_value_label = QLabel(f"{current_font_size}pt")
        
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value_label)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        
        # About
        self.help_card = HyperlinkCard("https://ximing766.github.io/my-project-doc/", "Open Help Page")
        self.feedback_card = PushSettingCard("Provide Feedback")
        self.feedback_card.clicked.connect(self.show_feedback_dialog)
        self.update_card = PushSettingCard("Check for Updates")
        self.update_card.clicked.connect(self.check_update)
        
        # Add all to layout
        content_layout.addWidget(self.theme_card)
        content_layout.addWidget(self.background_card)
        content_layout.addWidget(opacity_container)
        content_layout.addWidget(self.font_card)
        content_layout.addWidget(font_size_container)
        
        # Spacer
        content_layout.addSpacing(20)
        
        content_layout.addWidget(self.help_card)
        content_layout.addWidget(self.feedback_card)
        content_layout.addWidget(self.update_card)
        
        content_layout.addStretch()
        
        scroll_content.setLayout(content_layout)
        scroll_widget.setWidget(scroll_content)
        self.layout.addWidget(scroll_widget)
        
        # Set max width to make it look like a right menu
        self.setMaximumWidth(240)
    
    def on_theme_clicked(self):
        current_text = self.theme_card.button.text()
        # In PyDracula, theme names in settings.json usually match filenames in gui/themes/
        # Let's assume themes are "default" (Dark) and "bright_theme" (Light)
        themes_map = {
            "Light": "bright_theme",
            "Dark": "default"
        }
        
        next_display = "Dark" if current_text == "Light" else "Light"
        next_theme_file = themes_map[next_display]
        
        self.theme_card.button.setText(next_display)
        
        # 1. Update our ConfigManager
        if self.config_manager:
            self.config_manager.set_theme(next_display.lower())
            
        # 2. Update PyDracula's settings.json
        try:
            from gui.core.json_settings import Settings
            settings = Settings()
            settings.items["theme_name"] = next_theme_file
            settings.serialize()
            
            # 3. Notify MainWindow to reload theme
            if self.window() and hasattr(self.window(), "theme_changed"):
                self.window().theme_changed()
                
        except Exception as e:
            self.show_error("Error", f"Failed to change theme: {str(e)}")
    
    def cycle_background_image(self):
        if not self.config_manager:
            return
        available_images = self.config_manager.get_available_backgrounds()
        if not available_images:
            return
        
        current_index = self.config_manager.get_background_config().get("current_index", 0)
        next_index = (current_index + 1) % len(available_images)
        next_image = available_images[next_index]
        
        self.config_manager.set_current_background(next_image)
        self.config_manager.set_background_enabled(True)
        self.background_changed.emit(next_image)
    
    def on_opacity_changed(self, value: int):
        if self.config_manager:
            self.config_manager.set_background_opacity(value / 100.0)
        self.opacity_value_label.setText(f"{value}%")
        if self.window():
            self.window().update()
    
    def on_font_changed(self, new_family: str):
        """Handle font family change from combo box"""
        if not new_family or not self.config_manager:
            return
        self.config_manager.set_font_family(new_family)
        if self.window() and hasattr(self.window(), "apply_global_font"):
            self.window().apply_global_font()
    
    def on_font_size_changed(self, value: int):
        self.font_size_value_label.setText(f"{value}pt")
        if self.config_manager:
            self.config_manager.set_font_size(value)
            if self.window() and hasattr(self.window(), "apply_global_font"):
                self.window().apply_global_font()

    def show_feedback_dialog(self):
        self.show_info("Feedback", "Thank you for your interest in providing feedback!\n\nPlease visit our GitHub repository.")
    
    def check_update(self):
        self.update_card.button.setText("Checking...")
        self.update_card.button.setEnabled(False)
        
        self.update_thread = UpdateCheckerThread(GITHUB_REPO, APP_VERSION)
        self.update_thread.result_ready.connect(self._on_update_result)
        self.update_thread.error_occurred.connect(self._on_update_error)
        self.update_thread.finished.connect(lambda: self.update_card.button.setEnabled(True))
        self.update_thread.finished.connect(lambda: self.update_card.button.setText("Check for Updates"))
        self.update_thread.start()

    def _on_update_result(self, result):
        if result['has_update']:
            msg = f"A new version ({result['latest_version']}) is available!\n\nRelease Notes:\n{result['release_notes']}\n\nWould you like to download it?"
            
            # Show interactive dialog using the base page's standard method
            reply = self.show_warning(
                title="Update Available", 
                content=msg,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                default_button=QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl(result['download_url']))
        else:
            self.show_success("Up to Date", f"You are using the latest version (v{result['latest_version']}).")

    def _on_update_error(self, error_msg):
        self.show_error("Update Check Failed", f"Could not check for updates:\n{error_msg}")
    
    def show_about_dialog(self):
        self.show_info("About", f"Application Template\nVersion {APP_VERSION}\nAuthor: @Qilang²\nCopyright © 2024 | MIT License")
    
    def __str__(self):
        return f"SettingsPage(id='{self.page_id}')"