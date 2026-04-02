# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal

from database import DatabaseManager, UserDatabase, User


class UserSession:
    """Current user session information"""
    def __init__(self):
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.role: Optional[str] = None
        self.full_name: Optional[str] = None
        self.email: Optional[str] = None
        self.is_authenticated: bool = False
        self.login_time: Optional[datetime] = None

    def clear(self):
        """Clear session data"""
        self.user_id = None
        self.username = None
        self.role = None
        self.full_name = None
        self.email = None
        self.is_authenticated = False
        self.login_time = None

    def set_user(self, user: User):
        """Set session data from User object"""
        self.user_id = user.id
        self.username = user.username
        self.role = user.role
        self.full_name = user.full_name
        self.email = user.email
        self.is_authenticated = True
        self.login_time = datetime.now()

    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.role == 'admin'


class UserManager(QObject):
    """Manages user authentication and database operations"""
    user_logged_in = Signal(str)
    user_logged_out = Signal()
    user_created = Signal(str)
    user_updated = Signal(str)
    user_deleted = Signal(str)

    def __init__(self, config_dir: Optional[str] = None):
        super().__init__()

        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent

        self.config_dir.mkdir(exist_ok=True)

        self.db_manager = DatabaseManager()
        self.user_db = UserDatabase(self.db_manager)
        self.current_session = UserSession()

        self._create_default_users()

    def _create_default_users(self):
        """Create default admin and user accounts if they don't exist"""
        self.user_db.create_default_users()

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user with username and password"""
        user = self.user_db.authenticate_user(username, password)
        if user:
            self.current_session.set_user(user)
            self.user_logged_in.emit(username)
            return True
        return False

    def logout(self):
        """Logout current user"""
        if self.current_session.is_authenticated:
            self.current_session.clear()
            self.user_logged_out.emit()

    def create_user(self, username: str, password: str, email: str = "",
                   full_name: str = "", role: str = "user") -> bool:
        """Create a new user"""
        user = self.user_db.create_user(username, password, email, full_name, role)
        if user:
            self.user_created.emit(username)
            return True
        return False

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        username = None
        try:
            with self.user_db.db_manager.session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return False
                username = user.username
        except Exception as e:
            print(f"Error getting user for update: {e}")
            return False

        success = self.user_db.update_user(user_id, **kwargs)

        if success and username:
            self.user_updated.emit(username)

        return success

    def delete_user(self, user_id: int) -> bool:
        """Delete a user (soft delete by setting is_active=False)"""
        user = self.user_db.get_user_by_id(user_id)
        if not user or user.username == 'admin':
            return False

        username = user.username
        success = self.user_db.delete_user(user_id, soft_delete=True)

        if success:
            self.user_deleted.emit(username)

        return success

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        return self.user_db.get_all_users()

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.user_db.get_user_by_id(user_id)
        return user.to_dict() if user else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        user = self.user_db.get_user_by_username(username)
        return user.to_dict() if user else None

    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return self.user_db.user_exists(username)

    def get_user_count(self) -> int:
        """Get total user count"""
        return self.user_db.get_user_count()

    def is_user_management_enabled(self) -> bool:
        """Check if user management is enabled in config"""
        return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current logged in user info"""
        if self.current_session.is_authenticated:
            return {
                'id': self.current_session.user_id,
                'username': self.current_session.username,
                'role': self.current_session.role,
                'full_name': self.current_session.full_name,
                'email': self.current_session.email,
                'login_time': self.current_session.login_time.isoformat() if self.current_session.login_time else None
            }
        return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_session.is_authenticated

    def is_logged_in(self) -> bool:
        """Check if user is logged in (alias for is_authenticated)"""
        return self.is_authenticated()

    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.current_session.is_admin()

    def close(self):
        """Close database connections"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()

    def __del__(self):
        """Destructor to ensure database connections are closed"""
        self.close()