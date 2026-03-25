# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QWidget, QSlider
from PyQt6.QtGui import QDesktopServices
from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, PushSettingCard,
    HyperlinkCard, PrimaryPushSettingCard, SimpleCardWidget,
    FluentIcon as FIF, InfoBar, InfoBarPosition, MessageBox,
    ExpandLayout, ScrollArea, qconfig, Theme, setTheme,
    StrongBodyLabel, CaptionLabel
)
from .base_page import BasePage

class SettingsPage(BasePage):
    """Settings page with theme management and other general settings"""
    background_changed = pyqtSignal(str)  # Emitted when background changes

    def __init__(self, config_manager=None, parent=None):
        self.config_manager = config_manager
        self.user_manager = None
        super().__init__("settings", parent)
    
    def init_content(self):
        """Initialize page content"""
        scroll_widget = ScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container widget for scroll content
        scroll_content = QWidget()
        
        # Create vertical layout for settings groups (use QVBoxLayout instead of ExpandLayout)
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(20)  # Add spacing between groups
        content_layout.setContentsMargins(20, 20, 20, 20)  # Add margins
        
        # Create settings groups
        appearance_group = self.create_appearance_group()
        application_group = self.create_application_group()
        about_group = self.create_about_group()
        
        # Add groups to layout
        content_layout.addWidget(appearance_group)
        content_layout.addWidget(application_group)
        content_layout.addWidget(about_group)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        # Set the container as scroll widget content
        scroll_content.setLayout(content_layout)
        scroll_widget.setWidget(scroll_content)
        
        # Add scroll widget to main layout
        self.layout.addWidget(scroll_widget)
    
    def create_appearance_group(self):
        """Create appearance settings group"""
        group = SettingCardGroup("外观", self)
        
        # Get current theme from config
        current_theme = "Light"
        if self.config_manager:
            current_theme = self.config_manager.get_theme()
        
        # Theme setting card - use PushSettingCard instead of ComboBoxSettingCard
        self.theme_card = PushSettingCard(
            current_theme,
            FIF.BRUSH,
            "主题",
            "选择应用程序主题",
            parent=group
        )
        self.theme_card.clicked.connect(self.on_theme_clicked)
        
        # Background image card - directly cycle through background images
        self.background_card = PushSettingCard(
            "切换背景",
            FIF.PHOTO,
            "背景图片",
            "点击切换背景图片",
            parent=group
        )
        self.background_card.clicked.connect(self.cycle_background_image)
        
        # Opacity slider
        opacity_card = SimpleCardWidget(group)
        opacity_layout = QHBoxLayout(opacity_card)
        opacity_label = StrongBodyLabel("背景透明度", opacity_card)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, opacity_card)
        self.opacity_slider.setRange(0, 100)
        current_opacity = 100
        if self.config_manager:
            current_opacity = int(self.config_manager.get_background_opacity() * 100)
        self.opacity_slider.setValue(current_opacity)
        self.opacity_value_label = CaptionLabel(f"{current_opacity}%", opacity_card)
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider, 1)
        opacity_layout.addWidget(self.opacity_value_label)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        
        group.addSettingCard(self.theme_card)
        group.addSettingCard(self.background_card)
        group.addSettingCard(opacity_card)
        
        return group
    
    def create_application_group(self):
        group = SettingCardGroup("应用程序", self)
        
        # Language setting card
        self.language_card = PushSettingCard(
            "中文",
            FIF.LANGUAGE,
            "语言",
            "更改应用程序语言",
            parent=group
        )
        self.language_card.clicked.connect(self.on_language_clicked)
        
        # Reset settings card
        self.reset_card = PrimaryPushSettingCard(
            "重置",
            FIF.UPDATE,
            "重置设置",
            "将所有设置恢复为默认值",
            parent=group
        )
        self.reset_card.clicked.connect(self.reset_settings)
        
        group.addSettingCard(self.language_card)
        group.addSettingCard(self.reset_card)
        
        return group
    
    def create_about_group(self):
        """Create about settings group"""
        group = SettingCardGroup("关于", self)
        
        # Help card - fix HyperlinkCard parameter order
        self.help_card = HyperlinkCard(
            "https://ximing766.github.io/my-project-doc/",
            "打开帮助页面",
            FIF.HELP,
            "帮助",
            "发现新功能",
            parent=group
        )
        
        # Feedback card
        self.feedback_card = PushSettingCard(
            "提供反馈",
            FIF.FEEDBACK,
            "反馈",
            "提供反馈以帮助我们改进应用程序",
            parent=group
        )
        self.feedback_card.clicked.connect(self.show_feedback_dialog)
        
        # Check update card
        self.update_card = PushSettingCard(
            "检查更新",
            FIF.UPDATE,
            "软件更新",
            "检查并安装应用程序更新",
            parent=group
        )
        self.update_card.clicked.connect(self.check_update)
        
        # About card
        self.about_card = PushSettingCard(
            "关于应用",
            FIF.INFO,
            "关于",
            "版权所有 © 2024. 保留所有权利。",
            parent=group
        )
        self.about_card.clicked.connect(self.show_about_dialog)
        
        group.addSettingCard(self.help_card)
        group.addSettingCard(self.feedback_card)
        group.addSettingCard(self.update_card)
        group.addSettingCard(self.about_card)

        return group
    
    def on_theme_clicked(self):
        """Handle theme button click - cycle through themes"""
        current_text = self.theme_card.button.text()
        themes = ["Light", "Dark"]
        
        try:
            current_index = themes.index(current_text)
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]
        except ValueError:
            next_theme = "Light"  # Default fallback
        
        # Update button text
        self.theme_card.button.setText(next_theme)
        
        # Save to config first
        if self.config_manager:
            self.config_manager.set_theme(next_theme)

        if next_theme.lower() == "dark":
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
        
        self.show_success("Theme Changed", f"Theme changed to {next_theme}", 2000)
    
    def cycle_background_image(self):
        """Cycle through background images in assets/PIC folder"""
        if not self.config_manager:
            self.show_warning("配置错误", "配置管理器未初始化")
            return
        
        # Get available images from config manager (which reads from assets/PIC)
        available_images = self.config_manager.get_available_backgrounds()
        
        if not available_images:
            self.show_warning("无背景图片", "PIC 文件夹中没有找到图片文件")
            return
        
        # Get current background configuration
        current_image = self.config_manager.get_current_background()
        current_index = self.config_manager.get_background_config().get("current_index", 0)
        
        # Calculate next index
        next_index = (current_index + 1) % len(available_images)
        next_image = available_images[next_index]
        
        # Update button text to show current image name
        image_name = os.path.basename(next_image)
        self.background_card.setContent(f"当前: {image_name}")
        
        # Save to config
        self.config_manager.set_current_background(next_image)
        self.config_manager.set_background_enabled(True)
        
        # Emit signal
        self.background_changed.emit(next_image)
        
        # Show info
        self.show_success("背景已切换", f"背景图片已切换到 {image_name}", 2000)
    
    def on_opacity_changed(self, value: int):
        if self.config_manager:
            self.config_manager.set_background_opacity(value / 100.0)
        self.opacity_value_label.setText(f"{value}%")
        if self.window():
            self.window().update()
    
    def on_language_clicked(self):
        """Handle language button click - cycle through languages"""
        current_text = self.language_card.button.text()
        languages = ["English", "中文"]
        
        try:
            current_index = languages.index(current_text)
            next_index = (current_index + 1) % len(languages)
            next_language = languages[next_index]
        except ValueError:
            next_language = "English"  # Default fallback
        
        # Update button text
        self.language_card.button.setText(next_language)
        
        # Save to config
        if self.config_manager:
            self.config_manager.set_language(next_language.lower())
        
        self.show_info("Language Setting", f"待定...", 3000)
    
    def reset_settings(self):
        """Reset all settings to default"""
        msg_box = MessageBox(
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?\n\nThis action cannot be undone.",
            self
        )
        if msg_box.exec():
            pass

    def show_feedback_dialog(self):
        """Show feedback dialog"""
        self.show_info("Feedback", "Thank you for your interest in providing feedback!\n\nPlease visit our GitHub repository or contact us directly.", 4000)
    
    def check_update(self):
        """Check for updates"""
        self.show_info("Update Check", "You are using the latest version.\n\nVersion: 1.0.0", 3000)
    
    def show_about_dialog(self):
        """Show about dialog with application information"""
        about_text = """
        <h2 style="color:#08f">🚀 应用模板</h2>
        <p><b>版本</b> <span style="color:#666">1.0.0</span></p>
        <p><b>作者</b> <span style="color:#666">@Qilang²</span></p>
        <p><b>© 版权信息</b></p>
        <p style="font-size:13px;color:#999">
        版权所有 © 2024 | MIT 开源协议
        </p>
        """
        
        msg_box = MessageBox("关于应用", about_text, self)
        msg_box.yesButton.setText("确定")
        msg_box.cancelButton.hide()  # Hide cancel button for about dialog
        msg_box.exec()
    
    def on_activate(self):
        """Called when settings page is activated"""
        super().on_activate()
    
    def on_deactivate(self):
        """Called when settings page is deactivated"""
        super().on_deactivate()
        # Auto-save removed as per requirements
    
    def __str__(self):
        return f"SettingsPage(id='{self.page_id}')"
