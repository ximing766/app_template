# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QLineEdit, QComboBox, QMessageBox, QDialog,
                            QFormLayout, QDialogButtonBox, QHeaderView,
                            QFrame, QSpacerItem, QSizePolicy, QGroupBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QColor
from typing import Dict, Any, List, Optional
from pages import BasePage
from core.icons import icon_path, render_svg


class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None, is_edit=False):
        super().__init__(parent)
        self.user_data = user_data
        self.is_edit = is_edit
        self.parent_page = parent if hasattr(parent, 'user_manager') else None
        self.setWindowTitle("编辑用户" if is_edit else "创建用户")
        self.setFixedSize(420, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setup_ui()
        self.apply_dialog_style()
        if is_edit and user_data:
            self.load_user_data()

    def apply_dialog_style(self):
        is_light = True
        if self.parent_page and hasattr(self.parent_page, '_get_current_theme'):
            is_light = self.parent_page._get_current_theme().lower() == "light"

        bg = "#f8f9fb" if is_light else "#2c313c"
        fg = "#2c3e50" if is_light else "#e8ecf0"
        input_bg = "#ffffff" if is_light else "#21252b"
        input_border = "#d1d9e6" if is_light else "#3f444e"
        input_focus = "#568af2"
        btn_bg = "#568af2"
        btn_cancel_bg = "#e2e8f0" if is_light else "#3f444e"
        btn_cancel_fg = "#4a5568" if is_light else "#c3ccdf"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
            }}
            QLabel {{
                color: {fg};
                font-size: 13px;
                background: transparent;
            }}
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 8px 12px;
                color: {fg};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {input_focus};
            }}
            QLineEdit:disabled {{
                background-color: {"#f0f0f0" if is_light else "#1a1d23"};
                color: {"#999" if is_light else "#666"};
            }}
            QComboBox {{
                background-color: {input_bg};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 8px 12px;
                color: {fg};
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg};
                color: {fg};
                selection-background-color: {input_focus};
            }}
            #save_btn {{
                background-color: {btn_bg};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            #save_btn:hover {{
                background-color: #4a7ee0;
            }}
            #cancel_btn {{
                background-color: {btn_cancel_bg};
                color: {btn_cancel_fg};
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
            }}
            #cancel_btn:hover {{
                background-color: {"#d1d9e6" if is_light else "#4a505c"};
            }}
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 24, 28, 24)

        # Title
        title = QLabel("编辑用户信息" if self.is_edit else "创建新用户")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setFixedHeight(36)
        if self.is_edit:
            self.username_edit.setEnabled(False)
        form_layout.addRow("用户名:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("请输入密码" if not self.is_edit else "留空则不修改密码")
        self.password_edit.setFixedHeight(36)
        form_layout.addRow("密码:", self.password_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("请输入邮箱")
        self.email_edit.setFixedHeight(36)
        form_layout.addRow("邮箱:", self.email_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        self.role_combo.setFixedHeight(36)
        form_layout.addRow("角色:", self.role_combo)

        if self.is_edit:
            self.status_combo = QComboBox()
            self.status_combo.addItems(["启用", "禁用"])
            self.status_combo.setFixedHeight(36)
            form_layout.addRow("状态:", self.status_combo)

        layout.addLayout(form_layout)
        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setObjectName("cancel_btn")
        self.cancel_button.setFixedHeight(38)
        self.save_button = QPushButton("保存" if self.is_edit else "创建")
        self.save_button.setObjectName("save_btn")
        self.save_button.setFixedHeight(38)
        self.save_button.setDefault(True)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save_user)

    def save_user(self):
        is_valid, error_msg = self.validate_data()
        if not is_valid:
            if self.parent_page:
                self.parent_page.show_error("验证错误", error_msg)
            return
        user_data = self.get_user_data()
        if self.is_edit:
            kwargs = {
                'email': user_data.get('email', ''),
                'role': user_data.get('role', 'user'),
            }
            if user_data.get('password'):
                kwargs['password'] = user_data['password']
            if 'is_active' in user_data:
                kwargs['is_active'] = user_data['is_active']
            success = self.parent_page.user_manager.update_user(
                user_id=self.user_data['id'], **kwargs
            )
            if success:
                if self.parent_page:
                    self.parent_page.show_success("成功", f"用户 {self.user_data['username']} 更新成功")
                self.accept()
            else:
                if self.parent_page:
                    self.parent_page.show_error("失败", "更新用户失败")
        else:
            success = self.parent_page.user_manager.create_user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data.get('email', ''),
                role=user_data.get('role', 'user')
            )
            if success:
                if self.parent_page:
                    self.parent_page.show_success("成功", f"用户 {user_data['username']} 创建成功")
                self.accept()
            else:
                if self.parent_page:
                    self.parent_page.show_error("失败", "创建用户失败，用户名可能已存在")

    def load_user_data(self):
        if not self.user_data:
            return
        self.username_edit.setText(self.user_data.get('username', ''))
        self.email_edit.setText(self.user_data.get('email', ''))
        role = self.user_data.get('role', 'user')
        role_index = self.role_combo.findText(role)
        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)
        if self.is_edit and hasattr(self, 'status_combo'):
            is_active = self.user_data.get('is_active', True)
            status_text = "启用" if is_active else "禁用"
            status_index = self.status_combo.findText(status_text)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

    def get_user_data(self) -> Dict[str, Any]:
        data = {
            'username': self.username_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'role': self.role_combo.currentText()
        }
        password = self.password_edit.text()
        if password:
            data['password'] = password
        if self.is_edit and hasattr(self, 'status_combo'):
            data['is_active'] = self.status_combo.currentText() == "启用"
        return data

    def validate_data(self) -> tuple[bool, str]:
        username = self.username_edit.text().strip()
        if not username:
            return False, "用户名不能为空"
        if not self.is_edit:
            password = self.password_edit.text()
            if not password:
                return False, "密码不能为空"
            if len(password) < 6:
                return False, "密码长度至少6位"
        email = self.email_edit.text().strip()
        if email and '@' not in email:
            return False, "邮箱格式不正确"
        return True, ""


class UserManagementPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("user_management", parent)
        self.user_manager = None
        self.users_data = []
        if hasattr(self.parent(), 'user_manager'):
            self.user_manager = self.parent().user_manager

    def init_content(self):
        if hasattr(self.parent(), 'user_manager'):
            self.user_manager = self.parent().user_manager
        if self.user_manager:
            current_user = self.user_manager.get_current_user()
        self.setup_ui()
        self.load_users()
        if self.user_manager:
            self.user_manager.user_created.connect(self.on_user_changed)
            self.user_manager.user_updated.connect(self.on_user_changed)
            self.user_manager.user_deleted.connect(self.on_user_changed)

    def setup_ui(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        self.add_user_btn = QPushButton()
        self.add_user_btn.setFixedSize(36, 36)
        self.add_user_btn.setCursor(Qt.PointingHandCursor)
        self.add_user_btn.setToolTip("添加用户")
        self.add_user_btn.clicked.connect(self.add_user)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setToolTip("刷新")
        self.refresh_btn.clicked.connect(self.load_users)

        toolbar_layout.addWidget(self.add_user_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()
        self.layout.addLayout(toolbar_layout)

        self.users_table = QTableWidget(self)
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels(["ID", "用户名", "邮箱", "角色", "状态", "操作"])
        self.users_table.verticalHeader().hide()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.users_table.setFocusPolicy(Qt.NoFocus)
        self.apply_table_styling(self.users_table)
        header = self.users_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setFont(QFont('Consolas', 13, QFont.Weight.DemiBold))
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.users_table.setColumnWidth(5, 200)
        self.layout.addWidget(self.users_table)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-size: 11px; padding: 4px 0;")
        self.layout.addWidget(self.status_label)

        # Apply theme to toolbar buttons
        self._apply_toolbar_theme()

    def _apply_toolbar_theme(self):
        """Apply theme-aware icons and styling to toolbar buttons."""
        is_light = self._get_current_theme().lower() == "light"
        icon_color = "#4a5568" if is_light else "#c3ccdf"
        bg_hover = "#e2e8f0" if is_light else "rgba(255,255,255,0.1)"
        dpr = self.devicePixelRatioF() or 1.0

        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {bg_hover};
            }}
        """
        self.add_user_btn.setStyleSheet(btn_style)
        self.refresh_btn.setStyleSheet(btn_style)

        add_pm = render_svg(icon_path("icon_add_user.svg"), 20, icon_color, dpr)
        if not add_pm.isNull():
            self.add_user_btn.setIcon(QIcon(add_pm))
            self.add_user_btn.setIconSize(add_pm.size() / dpr)

        refresh_pm = render_svg(icon_path("icon_refresh.svg"), 20, icon_color, dpr)
        if not refresh_pm.isNull():
            self.refresh_btn.setIcon(QIcon(refresh_pm))
            self.refresh_btn.setIconSize(refresh_pm.size() / dpr)

    def apply_base_style(self, theme_name="dark"):
        """Override to also refresh table and toolbar theme."""
        super().apply_base_style(theme_name)
        if hasattr(self, 'users_table'):
            self.apply_table_styling(self.users_table)
        if hasattr(self, 'add_user_btn'):
            self._apply_toolbar_theme()

    def load_users(self):
        if not self.user_manager:
            return
        try:
            self.users_data = self.user_manager.get_all_users()
            self.populate_table()
            self.status_label.setText(f"已加载 {len(self.users_data)} 个用户")
        except Exception as e:
            self.show_error("错误", f"加载用户失败: {str(e)}")

    def populate_table(self):
        self.users_table.setRowCount(len(self.users_data))
        for row, user in enumerate(self.users_data):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
            role_item = QTableWidgetItem(user['role'])
            if user['role'] == 'admin':
                role_item.setBackground(QColor(173, 216, 230))
            self.users_table.setItem(row, 3, role_item)
            status_text = "启用" if user['is_active'] else "禁用"
            status_item = QTableWidgetItem(status_text)
            if not user['is_active']:
                status_item.setBackground(Qt.GlobalColor.lightGray)
            self.users_table.setItem(row, 4, status_item)
            self.create_action_buttons(row, user)

    def create_action_buttons(self, row: int, user: Dict[str, Any]):
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(8, 4, 8, 4)
        actions_layout.setSpacing(8)

        btn_style = """
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """

        edit_btn = QPushButton("编辑")
        edit_btn.setFixedHeight(28)
        edit_btn.setMinimumWidth(60)
        edit_btn.setStyleSheet(btn_style.format(bg="#4a9eff", fg="white", hover="#3a8eef"))
        edit_btn.clicked.connect(lambda: self.edit_user(user))

        actions_layout.addWidget(edit_btn)

        if user['username'] != 'admin':
            delete_btn = QPushButton("删除")
            delete_btn.setFixedHeight(28)
            delete_btn.setMinimumWidth(60)
            delete_btn.setStyleSheet(btn_style.format(bg="#e85d5d", fg="white", hover="#d04a4a"))
            delete_btn.clicked.connect(lambda: self.delete_user(user))
            actions_layout.addWidget(delete_btn)

        actions_layout.addStretch()
        self.users_table.setRowHeight(row, 42)
        self.users_table.setCellWidget(row, 5, actions_widget)

    def add_user(self):
        dialog = UserDialog(self, is_edit=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def edit_user(self, user: Dict[str, Any]):
        dialog = UserDialog(self, user_data=user, is_edit=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def delete_user(self, user: Dict[str, Any]):
        if user['username'] == 'admin':
            self.show_warning("警告", "无法删除管理员账号")
            return
        if self.show_confirmation_dialog("确认删除", f"确定要删除用户 {user['username']} 吗？\n此操作不可撤销。", is_warning=True):
            success = self.user_manager.delete_user(user['id'])
            if success:
                self.show_success("成功", f"用户 {user['username']} 已删除")
            else:
                self.show_error("错误", "删除用户失败")

    def on_user_changed(self, username: str):
        QTimer.singleShot(500, self.load_users)

    def on_activate(self):
        super().on_activate()
        if self.user_manager and self.user_manager.is_admin():
            self.load_users()

    def on_deactivate(self):
        super().on_deactivate()
