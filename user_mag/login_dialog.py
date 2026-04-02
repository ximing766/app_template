# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
import sys
import os
import math
from PySide6.QtCore import Qt, QSize, QRect, Signal, QTimer, QEventLoop, QPoint
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QPainterPath, QCursor
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QWidget, QSpacerItem, QSizePolicy, QDialog, QLineEdit, QCheckBox, QPushButton, QMessageBox, QFrame

# IMPORT ONEDARK COMPONENTS
from gui.widgets.py_window.py_window import PyWindow
from gui.widgets.py_title_bar.py_title_bar import PyTitleBar


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
        self.dragPos = QPoint()
        self.setupUI()
        self.setupWindow()
        
        # DYNAMIC GRADIENT TIMER
        self.gradient_timer = QTimer(self)
        self.gradient_timer.timeout.connect(self.update_gradient)
        self.gradient_timer.start(50) # Update every 50ms

    def setupUI(self):
        # MAIN LAYOUT
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # UI COMPATIBILITY FOR PyTitleBar
        self.ui = self
        self.central_widget_layout = self.main_layout

        # ADD PY WINDOW
        self.window = PyWindow(
            self,
            layout = Qt.Vertical,
            bg_color = "#1c1f25",
            border_radius = 10,
            border_size = 2,
            border_color = "#343b48",
            enable_shadow = True
        )
        self.main_layout.addWidget(self.window)

        # ADD TITLE BAR
        self.title_bar = PyTitleBar(
            self,
            self,
            logo_width = 100,
            bg_color = "transparent",
            div_color = "transparent",
            btn_bg_color = "transparent",
            btn_bg_color_hover = "rgba(255, 255, 255, 0.1)",
            btn_bg_color_pressed = "rgba(255, 255, 255, 0.05)",
            icon_color = "#f8f8f2",
            icon_color_hover = "#ffffff",
            icon_color_pressed = "#edf0f5",
            context_color = "#6c99f4",
            text_foreground = "#f8f8f2",
            radius = 8,
            font_family = "Segoe UI",
            title_size = 10,
            is_custom_title_bar = True
        )
        self.title_bar.set_title("Login")
        self.title_bar.setFixedHeight(42)
        self.window.layout.addWidget(self.title_bar)

        # LOGIN CONTENT WIDGET
        self.login_content = QWidget()
        self.login_content.setStyleSheet("background-color: transparent; color: #f8f8f2;")
        self.window.layout.addWidget(self.login_content)

        self.verticalLayout_2 = QVBoxLayout(self.login_content)
        self.verticalLayout_2.setContentsMargins(40, 20, 40, 40)
        self.verticalLayout_2.setSpacing(15)

        # LOGO
        self.label_2 = QLabel()
        self.label_2.setMinimumSize(QSize(100, 100))
        self.label_2.setMaximumSize(QSize(100, 100))
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            size = min(logo_pixmap.width(), logo_pixmap.height())
            mask = QPixmap(size, size)
            mask.fill(Qt.GlobalColor.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(Qt.GlobalColor.black)
            painter.drawEllipse(0, 0, size, size)
            painter.end()
            rounded_pixmap = QPixmap(size, size)
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, size, size, logo_pixmap)
            painter.end()
            self.label_2.setPixmap(rounded_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_2.setScaledContents(True)
        self.verticalLayout_2.addWidget(self.label_2, 0, Qt.AlignmentFlag.AlignHCenter)

        # SPACER
        self.verticalLayout_2.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # USERNAME
        self.username_edit = QLineEdit()
        self.username_edit.setClearButtonEnabled(True)
        self.username_edit.setFixedHeight(40)
        self.username_edit.setText("admin")
        self.username_edit.setStyleSheet("background-color: #b3bdc9; border: 1px solid #6177a5; border-radius: 5px; padding: 0 10px; color: #181817;")
        self.verticalLayout_2.addWidget(self.username_edit)

        # PASSWORD
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setClearButtonEnabled(True)
        self.password_edit.setFixedHeight(40)
        self.password_edit.setStyleSheet("background-color: #b3bdc9; border: 1px solid #6177a5; border-radius: 5px; padding: 0 10px; color: #181817;")
        self.verticalLayout_2.addWidget(self.password_edit)

        # REMEMBER ME
        self.remember_checkbox = QCheckBox()
        self.remember_checkbox.setChecked(True)
        self.remember_checkbox.setStyleSheet(" background-color: transparent; color: #131301;")
        self.verticalLayout_2.addWidget(self.remember_checkbox)

        # LOGIN BUTTON
        self.login_button = QPushButton()
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setFixedHeight(40)
        self.login_button.setStyleSheet("background-color: #568af2; color: white; border-radius: 5px; font-weight: bold;")
        self.login_button.setAutoDefault(False)
        self.login_button.setDefault(False)
        self.verticalLayout_2.addWidget(self.login_button)

        # FORGOT PASSWORD
        self.pushButton_2 = QPushButton()
        self.pushButton_2.setStyleSheet("background-color: transparent; color: #568af2; text-decoration: underline; border: none;")
        self.verticalLayout_2.addWidget(self.pushButton_2)

        self.retranslateUi()
        self.connect_signals()
        self.password_edit.setFocus()

    def retranslateUi(self):
        self.username_edit.setPlaceholderText("Username:")
        self.password_edit.setPlaceholderText("Password:")
        self.remember_checkbox.setText("Remember me")
        self.login_button.setText("LOGIN")
        self.pushButton_2.setText("Forgot password?")

    def setupWindow(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 500)
        self.setMinimumSize(400, 500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Center on screen
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def mousePressEvent(self, event):
        # Store current mouse position
        self.dragPos = event.globalPos()

    def update_gradient(self):  # BM 渐变动态背景
        # UPDATE GRADIENT ANGLE
        self._gradient_angle += 0.05
        if self._gradient_angle > 2 * math.pi:
            self._gradient_angle = 0
            
        # CALCULATE X, Y COORDINATES FOR ROTATION
        x1 = 0.5 + 0.5 * math.cos(self._gradient_angle)
        y1 = 0.5 + 0.5 * math.sin(self._gradient_angle)
        x2 = 0.5 + 0.5 * math.cos(self._gradient_angle + math.pi)
        y2 = 0.5 + 0.5 * math.sin(self._gradient_angle + math.pi)
        
        # APPLY NEW GRADIENT STYLESHEET
        gradient = f"qlineargradient(x1:{x1:.2f}, y1:{y1:.2f}, x2:{x2:.2f}, y2:{y2:.2f}, stop:0 #50caca, stop:1 #d385c2)"
        self.window.set_stylesheet(bg_color=gradient)

    def connect_signals(self):
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)

    def handle_login(self):
        # Prevent double triggering
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
        # BEAUTIFIED ERROR DISPLAY: Use a toast-style notification
        self.show_toast(message, "#e06c75") # OneDark Red
        self.login_button.setEnabled(True)
        self.login_button.setText("Login")

    def show_success(self, message: str):
        # BEAUTIFIED SUCCESS DISPLAY: Use a toast-style notification
        self.show_toast(message, "#98c379") # OneDark Green

    def show_toast(self, message: str, color: str):
        # Clear previous toast
        if self._current_toast:
            try:
                self._current_toast.hide()
                self._current_toast.deleteLater()
            except:
                pass

        toast = QLabel(message, self)
        self._current_toast = toast
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
            font-size: 13px;
        """)
        toast.adjustSize()
        
        # Position at the top of the dialog, below the title bar
        x = (self.width() - toast.width()) // 2
        y = 50 # Below title bar (height 42)
        toast.move(x, y)
        toast.show()
        
        # Simple timer to delete toast after 3 seconds
        QTimer.singleShot(3000, toast.deleteLater)

    def get_credentials(self) -> tuple[str, str]:
        return self.username_edit.text().strip(), self.password_edit.text()

    def clear_form(self):
        if not self.remember_checkbox.isChecked():
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
        self._authenticated = False
        self._current_username = None

    def show_login_dialog(self) -> bool:
        self.login = LoginDialog(self.parent)
        self.login.login_successful.connect(self.handle_login_attempt)
        result = self.login.exec()
        return result

    def handle_login_attempt(self, username: str):
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
