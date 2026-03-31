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


class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None, is_edit=False):
        super().__init__(parent)
        self.user_data = user_data
        self.is_edit = is_edit
        self.parent_page = parent if hasattr(parent, 'user_manager') else None
        self.setWindowTitle("编辑用户" if is_edit else "创建用户")
        self.setFixedSize(400, 300)
        self.setup_ui()
        if is_edit and user_data:
            self.load_user_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        if self.is_edit:
            self.username_edit.setEnabled(False)
        form_layout.addRow("用户名:", self.username_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("请输入密码" if not self.is_edit else "留空则不修改密码")
        form_layout.addRow("密码:", self.password_edit)
        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("请输入全名")
        form_layout.addRow("全名:", self.fullname_edit)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("请输入邮箱")
        form_layout.addRow("邮箱:", self.email_edit)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        form_layout.addRow("角色:", self.role_combo)
        if self.is_edit:
            self.status_combo = QComboBox()
            self.status_combo.addItems(["启用", "禁用"])
            form_layout.addRow("状态:", self.status_combo)
        layout.addLayout(form_layout)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("取消")
        self.save_button = QPushButton("保存" if self.is_edit else "创建")
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
            success = self.parent_page.user_manager.update_user(
                user_id=self.user_data['id'],
                username=user_data['username'],
                email=user_data.get('email', ''),
                full_name=user_data.get('full_name', ''),
                role=user_data.get('role', 'user'),
                password=user_data.get('password') if user_data.get('password') else None
            )
            if success:
                if self.parent_page:
                    self.parent_page.show_success("成功", f"用户 {self.user_data['username']} 更新成功")
                self.accept()
            else:
                if self.parent_page:
                    self.parent_page.show_error("失败", "更新用户失败")
        else:
            success = self.parent_page.user_manager.register_user(
                username=user_data['username'],
                password=user_data['password'],
                email=user_data.get('email', ''),
                full_name=user_data.get('full_name', ''),
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
        self.fullname_edit.setText(self.user_data.get('full_name', ''))
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
            'full_name': self.fullname_edit.text().strip(),
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
        self.add_user_btn = QPushButton("添加用户")
        self.add_user_btn.clicked.connect(self.add_user)
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_users)
        toolbar_layout.addWidget(self.add_user_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()
        self.layout.addLayout(toolbar_layout)
        self.users_table = QTableWidget(self)
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(["ID", "Name", "Full Name", "Email", "Role", "Status", "Actions"])
        self.users_table.verticalHeader().hide()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.resizeColumnsToContents()
        self.apply_table_styling(self.users_table)
        header = self.users_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setFont(QFont('Consolas', 13, QFont.Weight.DemiBold))
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.layout.addWidget(self.users_table)
        self.status_label = QLabel("就绪")
        self.layout.addWidget(self.status_label)

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
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get('full_name', '')))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.get('email', '')))
            role_item = QTableWidgetItem(user['role'])
            if user['role'] == 'admin':
                role_item.setBackground(QColor(173, 216, 230))
            self.users_table.setItem(row, 4, role_item)
            status_text = "启用" if user['is_active'] else "禁用"
            status_item = QTableWidgetItem(status_text)
            if not user['is_active']:
                status_item.setBackground(Qt.GlobalColor.lightGray)
            self.users_table.setItem(row, 5, status_item)
            self.create_action_buttons(row, user)

    def create_action_buttons(self, row: int, user: Dict[str, Any]):
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 2, 5, 2)
        actions_layout.setSpacing(5)
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(60, 25)
        edit_btn.clicked.connect(lambda: self.edit_user(user))
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(60, 25)
        delete_btn.setStyleSheet("QPushButton { background-color: #f34f4f; color: white;}")
        delete_btn.clicked.connect(lambda: self.delete_user(user))
        if user['username'] == 'admin':
            actions_layout.addWidget(edit_btn)
            self.users_table.setCellWidget(row, 6, actions_widget)
            return
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        self.users_table.setCellWidget(row, 6, actions_widget)

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
