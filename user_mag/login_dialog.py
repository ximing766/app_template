# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
# Pure PySide6 login dialog — no OneDark/PyDracula dependency.

import sys
import os
import math
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QEventLoop, QPoint
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QIcon
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout, QLabel, QWidget,
    QSpacerItem, QSizePolicy, QDialog, QLineEdit, QCheckBox,
    QPushButton, QFrame
)

# Background gradient animation: ~30 fps, one full sweep in ~2.2 s.
GRADIENT_INTERVAL_MS = 50
GRADIENT_STEP = 0.09


class LoginDialog(QDialog):
    login_successful = Signal(str)
    login_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = None
        self._event_loop = None
        self._dialog_result = None
        self._current_toast = None
        self._gradient_angle = 0
        self._drag_pos = QPoint()
        self._setup_ui()
        self._setup_window()

        # Dynamic gradient timer (~30 fps, full colour sweep every ~2.2 s)
        self._gradient_timer = QTimer(self)
        self._gradient_timer.setTimerType(Qt.PreciseTimer)
        self._gradient_timer.timeout.connect(self._update_gradient)
        self._gradient_timer.start(GRADIENT_INTERVAL_MS)

    def _setup_ui(self):
        self.setObjectName("LoginDialog")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container with border radius
        self._container = QFrame()
        self._container.setObjectName("login_container")
        main_layout.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(42)
        title_bar.setStyleSheet("background: transparent;")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(10, 0, 5, 0)
        tb_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #f8f8f2; border: none; font-size: 16px; border-radius: 4px; }
            QPushButton:hover { background: rgba(255,255,255,0.15); }
        """)
        close_btn.clicked.connect(self.close)
        tb_layout.addWidget(close_btn)
        container_layout.addWidget(title_bar)

        # Login content
        content = QWidget()
        content.setStyleSheet("background-color: transparent; color: #f8f8f2;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(50, 10, 50, 50)
        content_layout.setSpacing(12)

        # Logo
        self._logo_label = QLabel()
        self._logo_label.setFixedSize(80, 80)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            size = min(pixmap.width(), pixmap.height())
            rounded = QPixmap(size, size)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, size, size, pixmap)
            painter.end()
            self._logo_label.setPixmap(
                rounded.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self._logo_label.setAlignment(Qt.AlignCenter)
        self._logo_label.setScaledContents(True)
        content_layout.addWidget(self._logo_label, 0, Qt.AlignHCenter)

        # Title
        title_label = QLabel("Welcome to Login")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; background: transparent;")
        content_layout.addWidget(title_label)

        content_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        input_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.25);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                padding: 0 14px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit:focus {

                background-color: rgba(255, 255, 255, 0.35);
                outline: none;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.65);
            }
        """

        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setClearButtonEnabled(True)
        self.username_edit.setFixedHeight(44)
        # self.username_edit.setText("admin")
        self.username_edit.setPlaceholderText(" Username")
        self.username_edit.setStyleSheet(input_style)
        content_layout.addWidget(self.username_edit)

        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setClearButtonEnabled(True)
        self.password_edit.setFixedHeight(44)
        self.password_edit.setPlaceholderText(" Password")
        self.password_edit.setStyleSheet(input_style)
        content_layout.addWidget(self.password_edit)


        content_layout.addSpacerItem(QSpacerItem(20, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Login button
        self.login_button = QPushButton("LOGIN")
        self.login_button.setFixedHeight(44)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: rgba(86, 138, 242, 0.8);
                border: 1px solid rgba(86, 138, 242, 1);
            }
            QPushButton:pressed {
                background-color: rgba(86, 138, 242, 0.6);
            }
        """)
        self.login_button.setAutoDefault(False)
        self.login_button.setDefault(False)
        self.login_button.clicked.connect(self.handle_login)
        content_layout.addWidget(self.login_button)

        container_layout.addWidget(content)

        # Connect signals
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
        self.username_edit.setFocus()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(380, 480)
        self.setMinimumSize(380, 480)
        self.setMaximumSize(380, 480)
        self.setWindowModality(Qt.ApplicationModal)
        # Center on screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() // 2 - 190, screen.height() // 2 - 240)

    def _update_gradient(self):
        self._gradient_angle += GRADIENT_STEP
        if self._gradient_angle > 2 * math.pi:
            self._gradient_angle -= 2 * math.pi
        x1 = 0.5 + 0.5 * math.cos(self._gradient_angle)
        y1 = 0.5 + 0.5 * math.sin(self._gradient_angle)
        x2 = 0.5 + 0.5 * math.cos(self._gradient_angle + math.pi)
        y2 = 0.5 + 0.5 * math.sin(self._gradient_angle + math.pi)
        gradient = f"qlineargradient(x1:{x1:.2f}, y1:{y1:.2f}, x2:{x2:.2f}, y2:{y2:.2f}, stop:0 #50caca, stop:1 #d385c2)"
        self._container.setStyleSheet(f"""
            #login_container {{
                background: {gradient};
                border-radius: 10px;
                border: 2px solid rgba(255,255,255,0.1);
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            diff = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + diff)
            self._drag_pos = event.globalPosition().toPoint()

    def handle_login(self):
        if not self.login_button.isEnabled():
            return
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username:
            self.show_error("Please enter username")
            self.username_edit.setFocus()
            return
        if not password:
            self.show_error("Please enter password")
            self.password_edit.setFocus()
            return
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        self.login_successful.emit(username)

    def show_error(self, message: str):
        self._show_toast(message, "#e06c75")
        self.login_button.setEnabled(True)
        self.login_button.setText("LOGIN")

    def show_success(self, message: str):
        self._show_toast(message, "#98c379")

    def _show_toast(self, message: str, color: str):
        if self._current_toast:
            try:
                self._current_toast.hide()
                self._current_toast.deleteLater()
            except:
                pass
        toast = QLabel(message, self)
        self._current_toast = toast
        toast.setAlignment(Qt.AlignCenter)
        toast.setStyleSheet(f"""
            background-color: {color}; color: white; border-radius: 5px;
            padding: 8px 15px; font-weight: bold; font-size: 13px;
        """)
        toast.adjustSize()
        x = (self.width() - toast.width()) // 2
        toast.move(x, 50)
        toast.show()
        QTimer.singleShot(3000, toast.deleteLater)

    def get_credentials(self) -> tuple:
        return self.username_edit.text().strip(), self.password_edit.text()

    def clear_form(self):
        self.username_edit.clear()
        self.password_edit.clear()

    def accept(self):
        self._dialog_result = True
        if self._event_loop:
            self._event_loop.quit()
        super().accept()

    def exec(self):
        self._event_loop = QEventLoop()
        self._dialog_result = None
        self.show()
        if self._event_loop:
            self._event_loop.exec()
        return self._dialog_result if self._dialog_result is not None else False

    def closeEvent(self, event):
        self.clear_form()
        if self._event_loop:
            self._event_loop.quit()
        super().closeEvent(event)


class LoginController:
    def __init__(self, user_manager, parent=None):
        self.user_manager = user_manager
        self.parent = parent
        self.login = None

    def show_login_dialog(self) -> bool:
        self.login = LoginDialog(self.parent)
        self.login.login_successful.connect(self._handle_attempt)
        return self.login.exec()

    def _handle_attempt(self, username: str):
        if not self.login:
            return
        username, password = self.login.get_credentials()
        if self.user_manager.authenticate(username, password):
            self.login.show_success(f"Welcome, {username}!")
            self.login.accept()
        else:
            self.login.show_error("Username or password is incorrect")
            self.login.password_edit.clear()
            self.login.password_edit.setFocus()

    def is_authenticated(self) -> bool:
        return self.user_manager.is_authenticated()

    def get_current_user(self):
        return self.user_manager.get_current_user()


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    w = LoginDialog()
    w.show()
    app.exec()
