# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

import os
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel, QScrollArea, QFrame, QMessageBox, QPushButton
from PySide6.QtGui import QDesktopServices
from .base_page import BasePage

class SettingCardGroup(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8f8f2;")
        self.layout.addWidget(self.title_label)
        
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(5)
        self.layout.addLayout(self.cards_layout)

    def addSettingCard(self, card):
        self.cards_layout.addWidget(card)

class BaseSettingCard(QFrame):
    def __init__(self, title, description="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #2c313c;
                border-radius: 8px;
            }
            QLabel { background-color: transparent; }
        """)
        self.setMinimumHeight(60)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 10)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f8f8f2;")
        text_layout.addWidget(self.title_label)
        
        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setStyleSheet("font-size: 12px; color: #8a95aa;")
            text_layout.addWidget(self.desc_label)
            
        self.main_layout.addLayout(text_layout)
        self.main_layout.addStretch()

class PushSettingCard(QFrame):
    clicked = Signal()
    
    def __init__(self, button_text, title="", description="", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.button = QPushButton(button_text)
        self.button.setMinimumHeight(40)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #3f444e;
                color: #f8f8f2;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #4a505c; }
        """)
        self.button.clicked.connect(self.clicked.emit)
        self.main_layout.addWidget(self.button)
        
    def setContent(self, text):
        self.button.setText(text)

class HyperlinkCard(QFrame):
    def __init__(self, url, button_text, title="", description="", parent=None):
        super().__init__(parent)
        self.url = url
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.button = QPushButton(button_text)
        self.button.setMinimumHeight(40)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #568af2;
                text-decoration: underline;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { color: #6e9bf4; }
        """)
        self.button.clicked.connect(self.open_url)
        self.main_layout.addWidget(self.button)
        
    def open_url(self):
        QDesktopServices.openUrl(QUrl(self.url))

class SettingsPage(BasePage):
    """Settings page with theme management and other general settings"""
    background_changed = Signal(str) 

    def __init__(self, config_manager=None, parent=None):
        self.config_manager = config_manager
        self.user_manager = None
        super().__init__("settings", parent)
    
    def init_content(self):
        """Initialize page content"""
        self.apply_base_style()
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
        current_theme = "Light"
        if self.config_manager:
            current_theme = self.config_manager.get_theme()
        
        self.theme_card = PushSettingCard(current_theme)
        self.theme_card.clicked.connect(self.on_theme_clicked)
        
        self.background_card = PushSettingCard("BACKGROUND")
        self.background_card.clicked.connect(self.cycle_background_image)
        
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
        self.opacity_value_label.setStyleSheet("color: #f8f8f2; font-size: 14px;")
        self.opacity_value_label.setFixedWidth(40)
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value_label)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        # Application
        self.language_card = PushSettingCard("English")
        self.language_card.clicked.connect(self.on_language_clicked)
        
        self.reset_card = PushSettingCard("Reset")
        self.reset_card.button.setStyleSheet("""
            QPushButton {
                background-color: #e06c75;
                color: white;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #f07c85; }
        """)
        self.reset_card.clicked.connect(self.reset_settings)
        
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
        
        # Spacer
        content_layout.addSpacing(20)
        
        content_layout.addWidget(self.language_card)
        content_layout.addWidget(self.reset_card)
        
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
            settings = Settings()
            settings.items["theme_name"] = next_theme_file
            settings.serialize()
            
            # 3. Notify MainWindow to reload theme
            if self.window() and hasattr(self.window(), "theme_changed"):
                self.window().theme_changed()
                
            self.show_info("Theme Changed", f"Theme changed to {next_display}. Applied immediately.")
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
        
        image_name = os.path.basename(next_image)
        self.background_card.setContent(f"Current: {image_name}")
        
        self.config_manager.set_current_background(next_image)
        self.config_manager.set_background_enabled(True)
        self.background_changed.emit(next_image)
    
    def on_opacity_changed(self, value: int):
        if self.config_manager:
            self.config_manager.set_background_opacity(value / 100.0)
        self.opacity_value_label.setText(f"{value}%")
        if self.window():
            self.window().update()
    
    def on_language_clicked(self):
        current_text = self.language_card.button.text()
        languages = ["English", "中文"]
        try:
            current_index = languages.index(current_text)
            next_index = (current_index + 1) % len(languages)
            next_language = languages[next_index]
        except ValueError:
            next_language = "English"
        
        self.language_card.button.setText(next_language)
        if self.config_manager:
            self.config_manager.set_language(next_language.lower())
    
    def reset_settings(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Reset Settings")
        msg.setText("Are you sure you want to reset all settings to default values?\n\nThis action cannot be undone.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet(self._get_msg_box_style())
        reply = msg.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            pass

    def show_feedback_dialog(self):
        self.show_info("Feedback", "Thank you for your interest in providing feedback!\n\nPlease visit our GitHub repository.")
    
    def check_update(self):
        self.show_info("Update Check", "You are using the latest version.\n\nVersion: 1.0.0")
    
    def show_about_dialog(self):
        self.show_info("About", "Application Template\nVersion 1.0.0\nAuthor: @Qilang²\nCopyright © 2024 | MIT License")
    
    def __str__(self):
        return f"SettingsPage(id='{self.page_id}')"