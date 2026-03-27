# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QSplitter

class BasePage(QWidget):
    page_activated = Signal(str)  # Emitted when page becomes active
    page_deactivated = Signal(str)  # Emitted when page becomes inactive
    data_changed = Signal(str, object)  # Emitted when page data changes
    
    def __init__(self, page_id: str, parent=None):
        super().__init__(parent)
        
        self.page_id = page_id
        self._is_active = False
        self._is_initialized = False
        
        # Set object name for identification
        self.setObjectName(page_id)
        
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.init_content()

        self._is_initialized = True
    
    def init_content(self):
        """Initialize page content - override in subclasses"""
        pass

    def apply_base_style(self):
        """Apply base styles for common widgets"""
        base_qss = """
        QComboBox, QLineEdit, QCheckBox { color: #f8f8f2; }
        QLineEdit, QTextEdit { 
            background-color: rgba(36, 42, 56, 0.2); 
            border: 1px solid #313d4b; 
            border-radius: 1px; 
            padding: 3px; 
            color: #ffffff;
            selection-background-color: #088bef;
        }
        QLineEdit:focus, QTextEdit:focus { border: 1.5px solid #477faa; background-color: rgba(27, 32, 44, 0.99); }

        QCheckBox { spacing: 5px; }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid #888c96;
            background-color: #21252b;
        }
        QCheckBox::indicator:checked {
            background-color: #3e4451;
            border-color: #568af2;
        }
        QCheckBox::indicator:hover { border-color: #564463; }

        QPushButton { 
            background-color: #3f444e; 
            color: #f8f8f2; 
            border-radius: 5px; 
            border: none; 
            padding: 5px 15px;
        }
        QPushButton:hover { background-color: #4a505c; }
        QPushButton:pressed { background-color: #2c313c; }

        QComboBox { background-color: #3f444e; border-radius: 5px; border: none; padding-left: 10px; min-height: 30px; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background-color: #3f444e; color: #f8f8f2; selection-background-color: #568af2; }
        
        QSplitter::handle {
            background-color: #666c77;
            margin: 1px;
            border-radius: 1px;
        }
        QSplitter::handle:hover {
            background-color: #568af2;
        }
        QSplitter::handle:pressed {
            background-color: #568af2;
        }
        QSplitter::handle:horizontal {
            width: 1px;
        }
        QSplitter::handle:vertical {
            height: 1px;
        }

        /* QSlider - Minimalist Style */
        QSlider { background: transparent; }
        QSlider::groove:horizontal { background: #2c313a; height: 4px; border-radius: 2px; }
        QSlider::handle:horizontal { background: #568af2; width: 4px; height: 12px; margin: -4px 0; border-radius: 2px; }
        QSlider::sub-page:horizontal { background: #568af2; border-radius: 2px; }

        QSlider::groove:vertical { background: #2c313a; width: 4px; border-radius: 2px; }
        QSlider::handle:vertical { background: #568af2; width: 12px; height: 4px; margin: 0 -4px; border-radius: 2px; }
        QSlider::sub-page:vertical { background: #568af2; border-radius: 2px; }

        
        /* QScrollBar - Minimalist Style */
        QScrollBar:vertical {
            background: #1e2229;
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #568af2;
            min-height: 20px;
            border-radius: 4px;
            margin: 1px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            background: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar:horizontal {
            background: #1e2229;
            height: 8px;
            margin: 0px;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background: #568af2;
            min-width: 20px;
            border-radius: 4px;
            margin: 1px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            background: none;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        """
        self.setStyleSheet(base_qss)
        
        # Ensure child splitters inherit this style
        for splitter in self.findChildren(QSplitter):
            splitter.setStyleSheet(base_qss)

    def apply_table_styling(self, table_widget):
        dark_qss = """
        QTableWidget {
            background: transparent;
            gridline-color: rgba(71, 85, 105, 0.5);
            border: 1px solid #3f444e;
            border-radius: 5px;
            color: #f8f8f2;
        }
        
        QTableWidget::item {
            background-color: rgba(30, 41, 59, 0.55);
            padding: 5px;
        }
        
        QTableWidget::item:selected {
            background: rgba(86, 138, 242, 0.3);
            color: #ffffff;
        }
        
        QHeaderView::section {
            background: rgba(35, 44, 71, 0.9);
            color: rgb(221, 230, 241);
            font-weight: bold;
            font-size: 14px;
            padding: 5px;
            border: none;
            border-bottom: 1px solid #3f444e;
            border-right: 1px solid #3f444e;
        }
        """
        table_widget.setStyleSheet(dark_qss)
    
    def get_page_id(self) -> str:
        """Get page identifier"""
        return self.page_id
    
    def is_active(self) -> bool:
        """Check if page is currently active"""
        return self._is_active
    
    def is_initialized(self) -> bool:
        """Check if page is initialized"""
        return self._is_initialized
    
    def activate(self):
        """Activate the page - called when page becomes visible"""
        if not self._is_active:
            self._is_active = True
            self.on_activate()
            self.page_activated.emit(self.page_id)
    
    def deactivate(self):
        """Deactivate the page - called when page becomes hidden"""
        if self._is_active:
            self._is_active = False
            self.on_deactivate()
            self.page_deactivated.emit(self.page_id)
    
    def on_activate(self):
        """Called when page is activated - override in subclasses"""
        pass
    
    def on_deactivate(self):
        """Called when page is deactivated - override in subclasses"""
        pass
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.activate()
    
    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        self.deactivate()
    
    def __str__(self):
        return f"BasePage(id='{self.page_id}')"
    
    def __repr__(self):
        return self.__str__()
    
    def _get_msg_box_style(self):
        return """
        QMessageBox {
            background-color: #282c34;
            color: #f8f8f2;
            font-size: 14px;
        }
        QMessageBox QLabel {
            color: #f8f8f2;
        }
        QMessageBox QPushButton {
            background-color: #3f444e;
            color: #f8f8f2;
            border-radius: 5px;
            border: none;
            padding: 5px 15px;
            min-width: 60px;
        }
        QMessageBox QPushButton:hover {
            background-color: #4a505c;
        }
        QMessageBox QPushButton:pressed {
            background-color: #2c313c;
        }
        """

    # Information display methods
    def show_info(self, title: str = "Info", content: str = "", duration: int = 1000):
        """Show info message"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(content)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet(self._get_msg_box_style())
        msg.exec()
    
    def show_success(self, title: str = "Success", content: str = "", duration: int = 1000):
        """Show success message"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(content)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet(self._get_msg_box_style())
        msg.exec()
    
    def show_warning(self, title: str = "Warning", content: str = "", duration: int = 2000):
        """Show warning message"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(content)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet(self._get_msg_box_style())
        msg.exec()
    
    def show_error(self, title: str = "Error", content: str = "", duration: int = 2000):
        """Show error message"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(content)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setStyleSheet(self._get_msg_box_style())
        msg.exec()