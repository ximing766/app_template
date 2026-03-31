# -*- coding: utf-8 -*-

# Copyright (C) 2025  Qilang² <ximing766@gmail.com>

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QSplitter, QLabel
from PySide6.QtGui import QFont, QColor

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
    
    def _get_current_theme(self):
        """Get current theme from config manager"""
        try:
            # Try to get config manager from parent window
            window = self.window()
            if hasattr(window, 'config_manager'):
                return window.config_manager.get_theme()
        except:
            pass
        
        # Fall back to PyDracula settings
        try:
            from gui.core.json_settings import Settings
            settings = Settings()
            if "bright" in settings.items.get("theme_name", ""):
                return "light"
        except:
            pass
        
        return "dark"
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.init_content()

        self._is_initialized = True
        
        # Apply base style with current theme
        current_theme = self._get_current_theme()
        self.apply_base_style(current_theme)
        
        # Apply global font
        self.apply_global_font()
    
    def apply_global_font(self):
        """Apply global font to this page and all its children"""
        font_family = "Courier New"
        font_size = 10
        try:
            window = self.window()
            if hasattr(window, 'config_manager'):
                font_family = window.config_manager.get_font_family()
                font_size = window.config_manager.get_font_size()
        except:
            pass
        
        font = QFont(font_family, font_size)
        self.setFont(font)
        
        # Apply font to all children
        for child in self.findChildren(QWidget):
            child.setFont(font)
    
    def init_content(self):
        """Initialize page content - override in subclasses"""
        pass

    def apply_base_style(self, theme_name="dark"):
        """Apply base styles for common widgets based on theme"""
        # Determine if we should use light or dark theme
        is_light = theme_name.lower() == "light"
        
        # Color definitions based on theme
        colors = {
            "text": "#060E22" if is_light else "#F2F8F8",
            "bg_input": "rgba(231, 250, 247, 0.2)" if is_light else "rgba(36, 42, 56, 0.2)",
            "border_input": "#c3ccdf" if is_light else "#313d4b",
            "border_input_focus": "#568af2" if is_light else "#477faa",
            "bg_input_focus": "rgba(242, 238, 245, 0.99)" if is_light else "rgba(27, 32, 44, 0.99)",
            "bg_checkbox": "#ffffff" if is_light else "#21252b",
            "border_checkbox": "#A896AF" if is_light else "#98a6ca",
            "bg_checkbox_checked": "#a783cf" if is_light else "#4c6291",
            "border_checkbox_hover": "#8CB8FF" if is_light else "#564463",
            "bg_btn": "#ffffff" if is_light else "#3f444e",
            "bg_btn_hover": "#f5f6f9" if is_light else "#4a505c",
            "bg_btn_pressed": "#e2e9f7" if is_light else "#2c313c",
            "border_btn": "#c3ccdf" if is_light else "transparent",
            "accent": "#568af2",
            "bg_scrollbar": "#e2e9f7" if is_light else "#1e2229",
            "bg_scrollbar_handle": "#b0b5c0" if is_light else "#568af2",
            "splitter": "#c3ccdf" if is_light else "#666c77",
            "slider_groove": "#e2e9f7" if is_light else "#2c313a"
        }
        
        # In light mode, add a subtle border to buttons for better visibility
        btn_border_css = f"border: 1px solid {colors['border_btn']};" if is_light else "border: none;"
        
        base_qss = f"""
        QLabel {{ color: {colors['text']}; }}
        QComboBox, QLineEdit, QCheckBox {{ color: {colors['text']}; }}
        QLineEdit, QTextEdit {{ 
            background-color: {colors['bg_input']}; 
            border: 1px solid {colors['border_input']}; 
            border-radius: 4px; 
            padding: 4px; 
            color: {colors['text']};
            selection-background-color: {colors['accent']};
        }}
        QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid {colors['border_input_focus']}; background-color: {colors['bg_input_focus']}; }}

        QCheckBox {{ spacing: 5px; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {colors['border_checkbox']};
            background-color: {colors['bg_checkbox']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {colors['bg_checkbox_checked']};
            border-color: {colors['border_checkbox']};
        }}
        QCheckBox::indicator:hover {{ border-color: {colors['border_checkbox_hover']}; }}

        QPushButton {{ 
            background-color: {colors['bg_btn']}; 
            color: {colors['text']}; 
            border-radius: 5px; 
            {btn_border_css}
            padding: 5px 15px;
        }}
        QPushButton:hover {{ background-color: {colors['bg_btn_hover']}; }}
        QPushButton:pressed {{ background-color: {colors['bg_btn_pressed']}; }}

        QComboBox {{ background-color: {colors['bg_btn']}; border-radius: 5px; border: none; padding-left: 20px; }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{ background-color: {colors['bg_btn']}; color: {colors['text']}; selection-background-color: {colors['accent']}; }}
        
        QSplitter::handle {{
            background-color: {colors['splitter']};
            margin: 1px;
            border-radius: 1px;
        }}
        QSplitter::handle:hover {{
            background-color: {colors['accent']};
        }}
        QSplitter::handle:pressed {{
            background-color: {colors['accent']};
        }}
        QSplitter::handle:horizontal {{
            width: 1px;
        }}
        QSplitter::handle:vertical {{
            height: 1px;
        }}

        /* QSlider - Minimalist Style */
        QSlider {{ background: transparent; }}
        QSlider::groove:horizontal {{ background: {colors['slider_groove']}; height: 4px; border-radius: 2px; }}
        QSlider::handle:horizontal {{ background: {colors['accent']}; width: 4px; height: 12px; margin: -4px 0; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {colors['accent']}; border-radius: 2px; }}

        QSlider::groove:vertical {{ background: {colors['slider_groove']}; width: 4px; border-radius: 2px; }}
        QSlider::handle:vertical {{ background: {colors['accent']}; width: 12px; height: 4px; margin: 0 -4px; border-radius: 2px; }}
        QSlider::sub-page:vertical {{ background: {colors['accent']}; border-radius: 2px; }}

        
        /* QScrollBar - Minimalist Style */
        QScrollBar:vertical {{
            background: {colors['bg_scrollbar']};
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {colors['bg_scrollbar_handle']};
            min-height: 20px;
            border-radius: 4px;
            margin: 1px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {colors['bg_scrollbar']};
            height: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {colors['bg_scrollbar_handle']};
            min-width: 20px;
            border-radius: 4px;
            margin: 1px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            background: none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
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

    # Information display methods
    def _show_notification(self, title: str, content: str, bg_color: str, text_color: str = "#ffffff",
                          duration: int = 2000):
       
        toast = QWidget(self.window())
        toast.setObjectName("ToastWidget")
        toast.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        toast.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Use QHBoxLayout for perfect centering
        layout = QHBoxLayout(toast)
        layout.setContentsMargins(20, 15, 20, 15)
        
        label = QLabel(content)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        style = f"""
            QWidget#ToastWidget {{ 
                background-color: {bg_color}; 
                border: 1px solid rgba(0, 0, 0, 0.1); 
                border-radius: 8px;
            }}
            QLabel {{ 
                color: {text_color}; 
                font-family: "Segoe UI", "Microsoft YaHei";
                font-size: 16px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """
        toast.setStyleSheet(style)
        
        toast.show()
        toast.adjustSize()
        
        # Position at top-right of the window
        main_window = self.window()
        if main_window:
            rect = main_window.geometry()
            x = rect.right() - toast.width() - 25
            y = rect.top() + 50
            toast.move(x, y)
        
        # Use a more reliable closing method
        def close_and_destroy():
            if toast:
                toast.close()
                toast.deleteLater()
        
        QTimer.singleShot(duration, close_and_destroy)
        return toast

    def show_info(self, title: str = "Info", content: str = "", duration: int = 2000):
        self._show_notification(title, content, "#E1F0FF", "#005A9E", duration)
    
    def show_success(self, title: str = "Success", content: str = "", duration: int = 2000):
        self._show_notification(title, content, "#DFF6DD", "#0F5C2E", duration)
    
    def show_warning(self, title: str = "Warning", content: str = "", duration: int = 3000):
        return self._show_notification(title, content, "#FFF4CE", "#9D5D00", duration)
    
    def show_error(self, title: str = "Error", content: str = "", duration: int = 4000):
        self._show_notification(title, content, "#FDE7E9", "#A80000", duration)
        
    def show_confirmation_dialog(self, title: str, content: str, is_warning: bool = False) -> bool:
        box = QMessageBox(self.window())
        box.setWindowTitle(title)
        box.setText(content)
        
        # Apply modern styling
        is_light = self._get_current_theme().lower() == "light"
        bg_color = "#f0f2f5" if is_light else "#282c34"
        text_color = "#2c3e50" if is_light else "#abb2bf"
        btn_bg = "#ffffff" if is_light else "#3f444e"
        btn_hover = "#e2e8f0" if is_light else "#4a505c"
        btn_border = "#cbd5e1" if is_light else "#1e2229"
        
        style = f"""
            QMessageBox {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                min-width: 300px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text_color};
                border: 1px solid {btn_border};
                border-radius: 5px;
                padding: 6px 20px;
                min-width: 80px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """
        # box.setStyleSheet(style)
        
        # Disable standard icon
        box.setIcon(QMessageBox.Icon.NoIcon)
        
        # Customize buttons
        yes_btn = box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        no_btn = box.addButton("No", QMessageBox.ButtonRole.NoRole)
        box.setDefaultButton(yes_btn)
        
        # Add accent color to Yes button
        accent_bg = "#568af2" if not is_warning else "#e06c75"
        # yes_btn.setStyleSheet(f"""
        #     QPushButton {{
        #         background-color: {accent_bg};
        #         color: white;
        #         border: none;
        #     }}
        #     QPushButton:hover {{
        #         background-color: {'#4d7ce6' if not is_warning else '#d95a63'};
        #     }}
        # """)
        
        box.exec()
        return box.clickedButton() == yes_btn

