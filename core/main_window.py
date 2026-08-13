# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
# Pure PySide6 main window — no OneDark/PyDracula dependency.

from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QEvent, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QPainterPath
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame
)

from config.config_manager import ConfigManager
from pages import SettingsPage, PageManager
from core.constants import APP_VERSION
from .icons import icon_path as _icon_path, render_svg

# ---------------------------------------------------------------------------
# NavButton — icon button used in the left sidebar
# ---------------------------------------------------------------------------

class NavButton(QPushButton):
    """Navigation button with a crisp SVG icon for the left sidebar."""

    ICON_SIZE = 20

    def __init__(self, btn_id: str, icon_name: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName(btn_id)
        self.setToolTip(tooltip)
        self.setFixedSize(48, 48)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setAttribute(Qt.WA_Hover, True)  # reliable hover repaints
        self._icon_path = _icon_path(icon_name)
        self._is_active = False
        self._hover = False
        self._icon_color = "#c3ccdf"
        self._icon_color_active = "#ffffff"
        self._accent = "#568af2"

    def set_active(self, active: bool):
        if self._is_active != active:
            self._is_active = active
            self.setChecked(active)
            self.update()

    def set_colors(self, idle: str, active: str, accent: str):
        self._icon_color = idle
        self._icon_color_active = active
        self._accent = accent
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Background pill
        painter.setPen(Qt.NoPen)
        if self._is_active:
            painter.setBrush(QColor(self._accent))
        elif self._hover:
            painter.setBrush(QColor(255, 255, 255, 28))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(3, 3, -3, -3), 8, 8)

        # Crisp, tinted icon rendered at device resolution
        if self._icon_path:
            dpr = self.devicePixelRatioF()
            color = self._icon_color_active if self._is_active else self._icon_color
            pm = render_svg(self._icon_path, self.ICON_SIZE, color, dpr)
            if not pm.isNull():
                w = pm.width() / dpr
                h = pm.height() / dpr
                painter.drawPixmap(
                    int(round((self.width() - w) / 2)),
                    int(round((self.height() - h) / 2)),
                    pm,
                )
        painter.end()


# ---------------------------------------------------------------------------
# TitleBar — custom frameless title bar
# ---------------------------------------------------------------------------

class TitleBar(QWidget):
    """Custom title bar with drag-to-move and window controls."""
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    BTN_ICON_SIZE = 14

    def __init__(self, parent=None, title="", logo_path=""):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setObjectName("title_bar")
        # Keep the bar itself unpainted so the container/background shows through.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._parent_window = parent
        self._drag_pos = QPoint()
        self._icon_color = "#c3ccdf"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(8)

        # Logo — transparent background, no dark patch behind it
        self._logo_label = QLabel()
        self._logo_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self._logo_label.setStyleSheet("background: transparent; border: none;")
        if logo_path and Path(logo_path).exists():
            dpr = self.devicePixelRatioF() or 1.0
            src = QPixmap(logo_path)
            if not src.isNull():
                pm = src.scaled(
                    int(20 * dpr), int(20 * dpr),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation,
                )
                pm.setDevicePixelRatio(dpr)
                self._logo_label.setPixmap(pm)
                self._logo_label.setFixedSize(20, 20)
        layout.addWidget(self._logo_label, 0, Qt.AlignVCenter)

        # Title — transparent background
        self._title_label = QLabel(title)
        self._title_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self._title_label.setStyleSheet(
            "background: transparent; border: none; color: #e6ebf2; font-size: 13px; font-weight: 500;"
        )
        layout.addWidget(self._title_label, 0, Qt.AlignVCenter)
        layout.addStretch()

        # Window control buttons
        self._buttons = {}
        for key, icon_name, tooltip, signal_name, danger in [
            ("min", "icon_minimize.svg", "Minimize", "minimize_clicked", False),
            ("max", "icon_maximize.svg", "Maximize", "maximize_clicked", False),
            ("close", "icon_close.svg", "Close", "close_clicked", True),
        ]:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setFlat(True)
            hover = "#e06c75" if danger else "rgba(255,255,255,0.14)"
            press = "#c85860" if danger else "rgba(255,255,255,0.07)"
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; border-radius: 6px; }}
                QPushButton:hover {{ background: {hover}; }}
                QPushButton:pressed {{ background: {press}; }}
            """)
            btn.clicked.connect(getattr(self, signal_name))
            layout.addWidget(btn)
            self._buttons[key] = (btn, icon_name)

        self._max_btn = self._buttons["max"][0]
        self._refresh_button_icons()

    def _refresh_button_icons(self):
        """Re-render control icons crisply for the current DPI / theme color."""
        dpr = self.devicePixelRatioF() or 1.0
        for key, (btn, icon_name) in self._buttons.items():
            pm = render_svg(_icon_path(icon_name), self.BTN_ICON_SIZE, self._icon_color, dpr)
            if not pm.isNull():
                btn.setIcon(QIcon(pm))
                btn.setIconSize(QSize(self.BTN_ICON_SIZE, self.BTN_ICON_SIZE))

    def set_icon_color(self, color: str):
        self._icon_color = color
        self._refresh_button_icons()

    def set_max_icon(self, icon_name: str):
        self._buttons["max"] = (self._max_btn, icon_name)
        self._refresh_button_icons()

    def set_title(self, title: str):
        self._title_label.setText(title)

    def set_title_color(self, color: str):
        self._title_label.setStyleSheet(
            f"background: transparent; border: none; color: {color}; font-size: 13px; font-weight: 500;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            win = self._parent_window
            handle = win.windowHandle() if win else None
            # Native move: gives snap-to-edge and correct multi-monitor behaviour,
            # and restores a maximized window when dragged.
            if handle:
                handle.startSystemMove()
                event.accept()
                return
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        # Fallback for platforms without startSystemMove
        if event.buttons() & Qt.LeftButton and self._parent_window and not self._drag_pos.isNull():
            diff = event.globalPosition().toPoint() - self._drag_pos
            self._parent_window.move(self._parent_window.pos() + diff)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximize_clicked.emit()


# ---------------------------------------------------------------------------
# SettingsPanel — right-side slide-out panel for settings
# ---------------------------------------------------------------------------

class SettingsPanel(QFrame):
    """Slide-out settings panel docked on the right side."""

    WIDTH = 280

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.WIDTH)
        self.setObjectName("settings_panel")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 12)
        self._layout.setSpacing(8)

        self._header = QLabel("Settings")
        self._header.setObjectName("settings_header")
        self._header.setStyleSheet(
            "background: transparent; border: none; font-size: 14px; font-weight: 600;"
        )
        self._layout.addWidget(self._header)

        self._content = None
        self.hide()

    def set_content(self, widget: QWidget):
        if self._content is not None:
            self._layout.removeWidget(self._content)
            self._content.setParent(None)
        self._content = widget
        self._layout.addWidget(widget)

    def set_header_color(self, color: str):
        self._header.setStyleSheet(
            f"background: transparent; border: none; color: {color};"
            " font-size: 14px; font-weight: 600;"
        )

    def toggle(self):
        self.setVisible(not self.isVisible())


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, app_name="Generic App", logo_path=None, user_manager=None):
        super().__init__()

        self.app_name = app_name
        self.logo_path = logo_path
        self.setWindowTitle(self.app_name)

        if logo_path and Path(logo_path).exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.user_manager = user_manager
        self.config_manager = ConfigManager()
        self.page_manager = PageManager(parent=self)

        if self.user_manager:
            self.page_manager.set_user_manager(self.user_manager)

        self.splash_screen = None
        self.pages = {}
        self._nav_buttons = {}

        # Background
        self.background_cache = None
        self.last_window_size = QSize()

        # Frameless window
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui()

        QTimer.singleShot(100, self._init_ui)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Build the entire UI layout in pure PySide6."""
        # Central widget
        self._central = QWidget()
        self._central.setObjectName("central_bg")
        self.setCentralWidget(self._central)

        root_layout = QVBoxLayout(self._central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Outer container with rounded corners
        self._container = QFrame()
        self._container.setObjectName("app_container")
        root_layout.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar(self, title=self.app_name, logo_path=self.logo_path or "")
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.maximize_clicked.connect(self._toggle_maximize)
        self._title_bar.close_clicked.connect(self.close)
        container_layout.addWidget(self._title_bar)

        # Body: left nav + content + settings panel
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left navigation bar
        self._left_nav = QFrame()
        self._left_nav.setFixedWidth(58)
        self._left_nav.setObjectName("left_nav")
        self._nav_layout = QVBoxLayout(self._left_nav)
        self._nav_layout.setContentsMargins(4, 8, 4, 8)
        self._nav_layout.setSpacing(4)
        self._nav_layout.addStretch()  # push settings button to bottom later
        body_layout.addWidget(self._left_nav)

        # Content area (stacked widget)
        self._pages_stack = QStackedWidget()
        self._pages_stack.setObjectName("pages_stack")
        body_layout.addWidget(self._pages_stack, 1)

        # Settings panel (right)
        self._settings_panel = SettingsPanel()
        body_layout.addWidget(self._settings_panel)

        container_layout.addWidget(body, 1)

        # Status bar at the bottom
        self._status_bar = QFrame()
        self._status_bar.setObjectName("status_bar")
        self._status_bar.setFixedHeight(24)
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(12, 0, 12, 0)
        status_layout.setSpacing(16)

        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("status_text")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        self._status_version = QLabel(f"v{self._get_version()}")
        self._status_version.setObjectName("status_version")
        status_layout.addWidget(self._status_version)

        container_layout.addWidget(self._status_bar)

        # Apply dark theme stylesheet
        self._apply_window_style()

    @staticmethod
    def _get_version():
        return APP_VERSION

    def _apply_window_style(self, radius: int = None):
        theme = self.config_manager.get_theme()
        is_light = theme == "light"
        bg_enabled = self.config_manager.get_background_config().get("enabled", False)
        if radius is None:
            radius = 0 if self.isMaximized() else 10
        self._corner_radius = radius

        bg = "#f0f2f5" if is_light else "#282c34"
        border = "#c3ccdf" if is_light else "#181a1f"
        # Semi-transparent chrome so a background image reads through cleanly.
        if bg_enabled:
            nav_bg = "rgba(226, 230, 236, 0.35)" if is_light else "rgba(33, 37, 43, 0.35)"
            panel_bg = "rgba(226, 230, 236, 0.75)" if is_light else "rgba(33, 37, 43, 0.75)"
        else:
            nav_bg = "#e2e6ec" if is_light else "#21252b"
            panel_bg = nav_bg

        # When a background image is enabled, paintEvent draws it and the
        # container must stay transparent. Decided here, never in paintEvent.
        container_bg = "transparent" if bg_enabled else bg
        container_border = "none" if bg_enabled else f"1px solid {border}"
        self._container.setStyleSheet(f"""
            #app_container {{
                background-color: {container_bg};
                border: {container_border};
                border-radius: {radius}px;
            }}
        """)
        # Title bar stays fully transparent — no dark patch behind logo/title.
        self._title_bar.setStyleSheet("#title_bar { background: transparent; border: none; }")
        self._left_nav.setStyleSheet(f"""
            #left_nav {{
                background-color: {nav_bg};
                border: none;
            }}
        """)
        self._settings_panel.setStyleSheet(f"""
            #settings_panel {{
                background-color: {panel_bg};
                border: none;
                border-left: 1px solid {border};
            }}
        """)

        # Status bar styling
        status_bg = "rgba(226, 230, 236, 0.5)" if is_light else "rgba(30, 34, 41, 0.5)"
        status_fg = "#4a5568" if is_light else "#8b95a5"
        status_border_top = "#c3ccdf" if is_light else "#3f444e"
        if hasattr(self, '_status_bar'):
            self._status_bar.setStyleSheet(f"""
                #status_bar {{
                    background-color: {status_bg};
                    border-top: 1px solid {status_border_top};
                    border-bottom-left-radius: {radius}px;
                    border-bottom-right-radius: {radius}px;
                }}
                #status_text, #status_version {{
                    color: {status_fg};
                    font-size: 11px;
                    background: transparent;
                    border: none;
                }}
            """)

        # Theme-aware icon / text colors
        title_color = "#2c3e50" if is_light else "#e6ebf2"
        icon_color = "#4a5568" if is_light else "#c3ccdf"
        self._title_bar.set_title_color(title_color)
        self._title_bar.set_icon_color(icon_color)
        self._settings_panel.set_header_color(title_color)
        for btn in self._nav_buttons.values():
            btn.set_colors(icon_color, "#ffffff", "#568af2")
        if hasattr(self, "_settings_btn"):
            self._settings_btn.set_colors(icon_color, "#ffffff", "#568af2")

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_ui(self):
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.show()

        # Settings page in the right panel
        self.settings_page = SettingsPage(self.config_manager, self)
        self.settings_page.background_changed.connect(self._on_background_changed)
        self._settings_panel.set_content(self.settings_page)

        # Settings toggle lives at the bottom of the nav rail
        self._settings_btn = NavButton("btn_top_settings", "icon_settings.svg", "Settings")
        self._settings_btn.clicked.connect(self._toggle_settings)

        self._setup_navigation()

        # Navigate to first page
        visible_pages = self.page_manager.get_visible_pages()
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)
        if sorted_pages:
            self._navigate_to(sorted_pages[0][0])

        self._apply_window_style()
        self.apply_global_font()

    def _setup_navigation(self):
        """Populate left nav with buttons for each registered page."""
        while self._nav_layout.count():
            item = self._nav_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        self._nav_buttons.clear()

        visible_pages = self.page_manager.get_visible_pages()
        sorted_pages = sorted(visible_pages.items(), key=lambda x: x[1].order)

        for page_id, page_info in sorted_pages:
            icon_name = page_info.icon or "icon_widgets.svg"
            btn = NavButton(f"btn_{page_id}", icon_name, page_info.tooltip)
            btn.clicked.connect(lambda checked=False, pid=page_id: self._navigate_to(pid))
            self._nav_layout.addWidget(btn, 0, Qt.AlignHCenter)
            self._nav_buttons[page_id] = btn

        self._nav_layout.addStretch()
        self._nav_layout.addWidget(self._settings_btn, 0, Qt.AlignHCenter)

    def _navigate_to(self, page_id: str):
        """Navigate to a page by id."""
        if page_id not in self.pages:
            page_info = self.page_manager.get_page_info(page_id)
            if page_info:
                page_instance = page_info.create_instance(self)
                self._pages_stack.addWidget(page_instance)
                self.pages[page_id] = page_instance

        if page_id in self.pages:
            self._pages_stack.setCurrentWidget(self.pages[page_id])
            # Update nav button active states
            for pid, btn in self._nav_buttons.items():
                btn.set_active(pid == page_id)

    def _toggle_settings(self):
        self._settings_panel.toggle()
        self._settings_btn.set_active(self._settings_panel.isVisible())

    def _toggle_maximize(self):
        # changeEvent handles the corner radius and icon swap
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def theme_changed(self):
        """Handle theme toggle."""
        self._apply_window_style()
        theme_name = self.config_manager.get_theme()
        for page_instance in self.pages.values():
            if hasattr(page_instance, 'apply_base_style'):
                page_instance.apply_base_style(theme_name)
        if hasattr(self, 'settings_page'):
            self.settings_page.apply_base_style(theme_name)
        self.update()

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------

    def _on_background_changed(self, bg_path):
        self.background_cache = None
        self._apply_window_style()
        self.update()

    def paintEvent(self, event):
        bg_config = self.config_manager.get_background_config()
        if not bg_config.get('enabled', False):
            super().paintEvent(event)
            return

        if self.background_cache is None or self.size() != self.last_window_size:
            self._update_background_cache(bg_config)

        radius = getattr(self, "_corner_radius", 10)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Clip to the rounded window shape so the image never bleeds past corners
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, -1, -1).toRectF(), radius, radius)
        painter.setClipPath(path)

        theme = self.config_manager.get_theme()
        painter.fillRect(self.rect(), QColor("#f0f2f5" if theme == "light" else "#282c34"))

        if self.background_cache and not self.background_cache.isNull():
            painter.setOpacity(bg_config.get('opacity', 1.0))
            # Center the (expanded) pixmap instead of anchoring top-left
            pm = self.background_cache
            x = (self.width() - pm.width()) // 2
            y = (self.height() - pm.height()) // 2
            painter.drawPixmap(x, y, pm)
        painter.end()
        super().paintEvent(event)

    def _update_background_cache(self, bg_config):
        current_image = bg_config.get('current_image')
        if not current_image:
            return
        bg_path = Path(current_image)
        if not bg_path.is_absolute():
            app_dir = Path(__file__).parent.parent
            bg_path = app_dir / current_image
        if bg_path.exists():
            pixmap = QPixmap(str(bg_path))
            if not pixmap.isNull():
                self.background_cache = pixmap.scaled(
                    self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                self.last_window_size = self.size()

    # ------------------------------------------------------------------
    # Font
    # ------------------------------------------------------------------

    def apply_global_font(self):
        if not self.config_manager:
            return
        font_family = self.config_manager.get_font_family()
        font_size = self.config_manager.get_font_size()
        font = QFont(font_family, font_size)
        self.setFont(font)
        for page_instance in self.pages.values():
            if hasattr(page_instance, 'apply_global_font'):
                page_instance.apply_global_font()
            else:
                page_instance.setFont(font)

    # ------------------------------------------------------------------
    # Resize grips (frameless window edge resizing)
    # ------------------------------------------------------------------

    RESIZE_MARGIN = 8

    def _edges_at(self, pos):
        """Return the Qt.Edges flags for a point near the window border."""
        if self.isMaximized():
            return Qt.Edges()

        m = self.RESIZE_MARGIN
        rect = self.rect()
        x, y = pos.x(), pos.y()
        edges = Qt.Edges()
        if x <= m:
            edges |= Qt.LeftEdge
        elif x >= rect.width() - m:
            edges |= Qt.RightEdge
        if y <= m:
            edges |= Qt.TopEdge
        elif y >= rect.height() - m:
            edges |= Qt.BottomEdge
        return edges

    @staticmethod
    def _cursor_for_edges(edges):
        left = bool(edges & Qt.LeftEdge)
        right = bool(edges & Qt.RightEdge)
        top = bool(edges & Qt.TopEdge)
        bottom = bool(edges & Qt.BottomEdge)
        if (top and left) or (bottom and right):
            return Qt.SizeFDiagCursor
        if (top and right) or (bottom and left):
            return Qt.SizeBDiagCursor
        if left or right:
            return Qt.SizeHorCursor
        if top or bottom:
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edges = self._edges_at(event.position().toPoint())
            if edges:
                handle = self.windowHandle()
                if handle:
                    # Try native resize first; if it fails, fall back to manual.
                    if not handle.startSystemResize(edges):
                        self._resize_edges = edges
                        self._resize_origin = event.globalPosition().toPoint()
                        self._resize_geo = self.geometry()
                    event.accept()
                    return
        self._resize_edges = Qt.Edges()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        edges = getattr(self, '_resize_edges', Qt.Edges())
        if edges and event.buttons() & Qt.LeftButton:
            # Manual resize fallback
            delta = event.globalPosition().toPoint() - self._resize_origin
            geo = self._resize_geo
            new_geo = geo.adjusted(0, 0, 0, 0)
            if edges & Qt.LeftEdge:
                new_geo.setLeft(geo.left() + delta.x())
            if edges & Qt.RightEdge:
                new_geo.setRight(geo.right() + delta.x())
            if edges & Qt.TopEdge:
                new_geo.setTop(geo.top() + delta.y())
            if edges & Qt.BottomEdge:
                new_geo.setBottom(geo.bottom() + delta.y())
            # Clamp to minimum
            if new_geo.width() >= self.minimumWidth() and new_geo.height() >= self.minimumHeight():
                self.setGeometry(new_geo)
            event.accept()
            return
        self.setCursor(self._cursor_for_edges(self._edges_at(event.position().toPoint())))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resize_edges = Qt.Edges()
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        self.background_cache = None
        super().resizeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange and hasattr(self, "_container"):
            maximized = self.isMaximized()
            self._title_bar.set_max_icon(
                "icon_restore.svg" if maximized else "icon_maximize.svg"
            )
            self._apply_window_style(radius=0 if maximized else 10)
        super().changeEvent(event)

    def set_status_message(self, message: str):
        """Set the status bar message text."""
        if hasattr(self, '_status_label'):
            self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self.config_manager.save_config()
        super().closeEvent(event)

