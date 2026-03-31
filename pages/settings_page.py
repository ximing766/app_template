# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
import os
import json
import urllib.request
from PySide6.QtCore import Qt, Signal, QUrl, QThread
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSlider, QLabel, QScrollArea, QFrame, QMessageBox, QPushButton, QComboBox
from PySide6.QtGui import QDesktopServices
from .base_page import BasePage
from core.pyupdate import UpdateManager
from core.constants import APP_VERSION, GITHUB_REPO


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
        self.combo.setEditable(True)
        self.combo.lineEdit().setReadOnly(True)
        self.combo.lineEdit().setAlignment(Qt.AlignCenter)
        self.combo.lineEdit().setStyleSheet("background: transparent; border: none; selection-background-color: transparent;")
        # Override the base page style to show the drop-down arrow
        self.combo.setStyleSheet("""

            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid currentColor;  /* 仅上边框着色，形成向下箭头 */
                margin-right: 8px;  /* 微调箭头和右边缘的距离 */
            }
        """)

        
        if items:
            self.combo.addItems(items)
        self.main_layout.addWidget(self.combo)


class SettingsPage(BasePage):
    background_changed = Signal(str)

    def __init__(self, config_manager=None, parent=None):
        self.config_manager = config_manager
        self.user_manager = None
        super().__init__("settings", parent)

    def init_content(self):
        scroll_widget = QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_widget.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QWidget#scroll_content { background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scroll_content")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 10, 0, 10)
        current_theme_display = "Dark"
        current_theme_name = "dark"

        if self.config_manager:
            current_theme_name = self.config_manager.get_theme()
            current_theme_display = "Light" if current_theme_name == "light" else "Dark"
        else:
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

        fonts = ["Consolas", "Courier New", "Lucida Console", "JetBrains Mono", "Cascadia Code"]
        self.font_card = ComboSettingCard(fonts)
        self.font_combo = self.font_card.combo
        current_font_family = "Courier New"
        if self.config_manager:
            current_font_family = self.config_manager.get_font_family()
        index = self.font_combo.findText(current_font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        self.font_combo.currentTextChanged.connect(self.on_font_changed)

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

        self.help_card = PushSettingCard("About")
        self.help_card.clicked.connect(self.show_about_dialog)
        self.feedback_card = PushSettingCard("Provide Feedback")
        self.feedback_card.clicked.connect(self.show_feedback_dialog)

        self.update_card = PushSettingCard("Check for Updates")  # BM update
        self.update_card.clicked.connect(self.check_update)

        content_layout.addWidget(self.theme_card)
        content_layout.addWidget(self.background_card)
        content_layout.addWidget(opacity_container)
        content_layout.addWidget(self.font_card)
        content_layout.addWidget(font_size_container)

        content_layout.addSpacing(20)
        content_layout.addWidget(self.help_card)
        content_layout.addWidget(self.feedback_card)
        content_layout.addWidget(self.update_card)

        content_layout.addStretch()

        scroll_content.setLayout(content_layout)
        scroll_widget.setWidget(scroll_content)
        self.layout.addWidget(scroll_widget)

    def on_theme_clicked(self):
        current_text = self.theme_card.button.text()
        themes_map = {"Light": "bright_theme", "Dark": "default"}
        next_display = "Dark" if current_text == "Light" else "Light"
        next_theme_file = themes_map[next_display]
        self.theme_card.button.setText(next_display)
        if self.config_manager:
            self.config_manager.set_theme(next_display.lower())
        try:
            from gui.core.json_settings import Settings
            settings = Settings()
            settings.items["theme_name"] = next_theme_file
            settings.serialize()
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

    def check_update(self):
        self.update_card.button.setText("Checking...")
        self.update_card.button.setEnabled(False)
        self.update_manager = UpdateManager(GITHUB_REPO, APP_VERSION)
        self.update_manager.set_mode("check")
        self.update_manager.update_finished.connect(self._on_check_finished)
        self.update_manager.start()

    def _on_check_finished(self, success, message):
        self.update_card.button.setEnabled(True)
        self.update_card.button.setText("Check for Updates")
        if not success:
            self.show_error("Update Check Failed", f"Could not check for updates:\n{message}")
            return
        result = self.update_manager.update_data
        if result.get('has_update'):
            msg = f"A new version ({result.get('latest_version')}) is available!\n\nRelease Notes:\n{result.get('release_notes')}\n\nWould you like to download and install it?"
            if self.show_confirmation_dialog("Update Available", msg):
                self.start_download()
        else:
            self.show_success("Up to Date", f"You are using the latest version (v{result.get('latest_version')}).")

    def start_download(self):
        self.update_card.button.setText("Downloading... 0%")
        self.update_card.button.setEnabled(False)
        self.update_manager.set_mode("download")
        try:
            self.update_manager.update_finished.disconnect()
        except:
            pass
        self.update_manager.update_finished.connect(self._on_download_finished)
        self.update_manager.progress_changed.connect(self._on_download_progress)
        self.update_manager.status_changed.connect(lambda s: self.update_card.button.setText(s))
        self.update_manager.start()

    def _on_download_progress(self, progress):
        self.update_card.button.setText(f"Downloading... {progress}%")

    def _on_download_finished(self, success, extracted_path):
        self.update_card.button.setEnabled(True)
        self.update_card.button.setText("Check for Updates")
        if not success:
            self.show_error("Download Failed", f"Could not download update:\n{extracted_path}")
            return
        if self.show_confirmation_dialog("Download Complete", "Update downloaded successfully. Restart the application to apply the update now?"):
            self.update_manager.set_mode("apply", update_data=extracted_path)
            self.update_manager.start()

    def show_feedback_dialog(self):
        self.show_info("Feedback", "Thank you for your interest in providing feedback!\n\nPlease visit our GitHub repository.")

    def show_about_dialog(self):
        self.show_confirmation_dialog("About", f"Application Template\nVersion {APP_VERSION}\nAuthor: @Qilang²\nCopyright © 2024 | MIT License")

    def __str__(self):
        return f"SettingsPage(id='{self.page_id}')"
