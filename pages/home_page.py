# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QFrame

from .base_page import BasePage
from core.constants import APP_NAME, APP_VERSION


class HomePage(BasePage):
    """Minimal placeholder page — replace with your own content."""

    def __init__(self, parent=None):
        super().__init__("home", parent)

    def init_content(self):
        card = QFrame()
        card.setObjectName("home_card")
        card.setStyleSheet("""
            #home_card {
                background-color: rgba(40, 44, 52, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignCenter)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 600; background: transparent;")
        card_layout.addWidget(title)

        version = QLabel(f"v{APP_VERSION}")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-size: 13px; color: #7f8794; background: transparent;")
        card_layout.addWidget(version)

        hint = QLabel("Register your pages in main.py to get started.")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #9aa3b0; background: transparent;")
        card_layout.addWidget(hint)

        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(24, 24, 24, 24)
        wrapper.addStretch()
        wrapper.addWidget(card, 0, Qt.AlignCenter)
        wrapper.addStretch()

        self.layout.addLayout(wrapper)
