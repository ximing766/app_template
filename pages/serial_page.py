# -*- coding: utf-8 -*-
"""Serial port page for production testing.

One control row is generated per detected serial port. Rows refresh
automatically while the page is visible; connections are only closed by the
user or when the device reports an error/loss — navigating away never closes
a port.

The console at the bottom mirrors the traffic of the first connected port; when
that port is closed, the next connected port takes over.
"""

import os
import re
import time

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from pages.base_page import BasePage
from serial_comm.port_scanner import PortScanner
from serial_comm.serial_config import COMMON_BAUDRATES, SerialConfig
from serial_comm.serial_manager import SerialManager

DEFAULT_BAUDRATE = 115200
REFRESH_INTERVAL_MS = 2000
MAX_LOG_BLOCKS = 2000

# Theme tokens shared with the rest of the app (home card / settings page look).
CARD_COLORS = {
    False: {"bg": "rgba(40, 44, 52, 0.55)", "border": "rgba(255, 255, 255, 0.08)",
            "muted": "#9aa3b0", "log_text": "#c3ccdf"},
    True: {"bg": "rgba(255, 255, 255, 0.65)", "border": "rgba(0, 0, 0, 0.08)",
           "muted": "#6b7280", "log_text": "#2c3e50"},
}
STATUS_COLORS = {
    False: {"on": "#4CAF50", "off": "#9aa3b0", "error": "#e06c75", "warn": "#e5c07b"},
    True: {"on": "#2e7d32", "off": "#7f8794", "error": "#c62828", "warn": "#b26a00"},
}

_CHEVRON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "images", "svg_icons", "icon_chevron_down.svg",
).replace("\\", "/")


class SerialPortRow(QFrame):
    """Control row for a single serial port."""

    connect_requested = Signal(str)      # port name
    disconnect_requested = Signal(str)   # port name

    def __init__(self, port_name: str, description: str, baudrates, current_baud: int,
                 is_light: bool = False, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.port_id = None
        self._status = "off"          # off | on | error | warn
        self._is_light = is_light
        self._detected = True

        self.setObjectName("serial_port_row")
        self.setFrameShape(QFrame.NoFrame)
        self._build_ui(description, baudrates, current_baud)
        self.apply_theme(is_light)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self, description: str, baudrates, current_baud: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.status_dot = QLabel("●")
        self.status_dot.setFixedWidth(14)
        self.status_dot.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_dot)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.name_label = QLabel(self.port_name)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        text_layout.addWidget(self.name_label)

        self.desc_label = QLabel(description or "Serial device")
        self.desc_label.setStyleSheet("font-size: 11px; background: transparent;")
        text_layout.addWidget(self.desc_label)

        layout.addLayout(text_layout, 1)

        self.baud_combo = QComboBox()
        self.baud_combo.setEditable(True)
        self.baud_combo.setFixedWidth(110)
        self.baud_combo.setMinimumHeight(32)
        self.baud_combo.setValidator(QIntValidator(50, 4000000, self.baud_combo))
        self.baud_combo.lineEdit().setAlignment(Qt.AlignCenter)
        self.baud_combo.lineEdit().setStyleSheet(
            "background: transparent; border: none; selection-background-color: transparent;"
        )
        # Base page QSS pads combos by 20px on the left; the value is centered
        # here so the padding only makes it look shifted.
        self.baud_combo.setStyleSheet(
            "QComboBox { padding-left: 4px; padding-right: 4px; }"
            "QComboBox::drop-down { border: none; width: 20px; }"
            f"QComboBox::down-arrow {{ image: url('{_CHEVRON_PATH}'); width: 10px; height: 6px; "
            "margin-right: 4px; }"
        )
        for baud in baudrates:
            self.baud_combo.addItem(str(baud), baud)
        self.baud_combo.setEditText(str(current_baud))
        layout.addWidget(self.baud_combo)

        self.action_btn = QPushButton("Connect")
        self.action_btn.setFixedWidth(110)
        self.action_btn.setMinimumHeight(32)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_btn)

    def _on_action_clicked(self):
        if self.port_id:
            self.disconnect_requested.emit(self.port_name)
        else:
            self.connect_requested.emit(self.port_name)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def baudrate(self) -> int:
        """Current baudrate typed/selected by the user."""
        try:
            value = int(self.baud_combo.currentText().strip())
            if 50 <= value <= 4000000:
                return value
        except (TypeError, ValueError):
            pass
        return DEFAULT_BAUDRATE

    def set_connected(self, port_id: str):
        self.port_id = port_id
        self._status = "on"
        self.baud_combo.setEnabled(False)
        self.action_btn.setText("Disconnect")
        self._refresh()

    def set_disconnected(self, status: str = "off"):
        self.port_id = None
        self._status = status
        self.baud_combo.setEnabled(True)
        self.action_btn.setText("Connect")
        self._refresh()

    def set_detected(self, detected: bool, description: str = ""):
        self._detected = detected
        if description:
            self.desc_label.setText(description)
        if not self.port_id:
            self.name_label.setEnabled(detected)
        self._refresh()

    def apply_theme(self, is_light: bool):
        self._is_light = is_light
        colors = CARD_COLORS[is_light]
        self.setStyleSheet(
            f"#serial_port_row {{ background-color: {colors['bg']}; "
            f"border: 1px solid {colors['border']}; border-radius: 10px; }}"
        )
        self.desc_label.setStyleSheet(
            f"font-size: 11px; color: {colors['muted']}; background: transparent;"
        )
        self._refresh()

    def _refresh(self):
        colors = STATUS_COLORS[self._is_light]
        if not self._detected and not self.port_id:
            self.status_dot.setStyleSheet(f"color: {colors['warn']}; background: transparent;")
        else:
            self.status_dot.setStyleSheet(f"color: {colors[self._status]}; background: transparent;")
        self.status_dot.setToolTip(self._status_text())

    def _status_text(self) -> str:
        if self.port_id:
            return f"Connected ({self.port_id})"
        if not self._detected:
            return "Not detected"
        if self._status == "error":
            return "Error"
        return "Disconnected"


class SerialPage(BasePage):
    """Serial port management page (auto-generated rows per detected port)."""

    def __init__(self, parent=None):
        super().__init__("serial", parent)

        self.serial_manager = SerialManager.instance()
        self._rows = {}         # port name -> SerialPortRow
        self._open_ports = {}   # port name -> port_id (insertion order == connect order)
        self._baud_prefs = {}   # port name -> baudrate
        self._log_port_id = None

        # Scanning happens off the GUI thread; results arrive via a signal.
        self._scanner = PortScanner(REFRESH_INTERVAL_MS, self)
        self._scanner.ports_found.connect(self._on_ports_found)
        self._scanner.scan_failed.connect(self._on_scan_failed)

        self._connect_manager_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def init_content(self):
        container = QVBoxLayout()
        container.setContentsMargins(4, 12, 4, 12)
        container.setSpacing(10)

        container.addWidget(self._build_header())

        # Scrollable port rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        scroll.viewport().setAutoFillBackground(False)

        rows_content = QWidget()
        rows_content.setObjectName("serial_scroll_content")
        rows_content.setStyleSheet("#serial_scroll_content { background: transparent; }")

        rows_layout = QVBoxLayout(rows_content)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(8)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(8)
        rows_layout.addLayout(self._rows_layout)

        self._empty_hint = QLabel(
            "No serial ports detected.\n"
            "Connect a device — the list refreshes automatically."
        )
        self._empty_hint.setAlignment(Qt.AlignCenter)
        self._empty_hint.setMinimumHeight(100)
        rows_layout.addWidget(self._empty_hint)

        self._summary = QLabel("")
        self._summary.setStyleSheet("font-size: 11px; background: transparent;")
        rows_layout.addWidget(self._summary)

        rows_layout.addStretch()
        scroll.setWidget(rows_content)
        container.addWidget(scroll, 1)

        container.addWidget(self._build_console(), 0)
        self.layout.addLayout(container)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("serial_header")
        # Selector-scoped: a bare "background: transparent" would cascade onto
        # the Refresh button and erase its background.
        header.setStyleSheet("#serial_header { background: transparent; }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        title = QLabel("Serial Ports")
        title.setStyleSheet("font-size: 18px; font-weight: 600; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(90)
        self.refresh_btn.setMinimumHeight(32)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._refresh_ports)
        header_layout.addWidget(self.refresh_btn)

        return header

    def _build_console(self) -> QWidget:
        card = QFrame()
        card.setObjectName("serial_console_card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 10, 16, 12)
        card_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        self._console_title = QLabel("Console")
        self._console_title.setStyleSheet(
            "font-size: 12px; font-weight: 600; background: transparent;"
        )
        title_row.addWidget(self._console_title)
        title_row.addStretch()

        # HEX keeps every byte visible (0x0A / 0x0D never become line breaks).
        self._hex_view = QCheckBox("HEX")
        self._hex_view.setCursor(Qt.PointingHandCursor)
        self._hex_view.setToolTip("Show raw bytes instead of decoded text")
        self._hex_view.toggled.connect(self._on_view_mode_changed)
        title_row.addWidget(self._hex_view)

        card_layout.addLayout(title_row)

        self._console = QPlainTextEdit()
        self._console.setObjectName("serial_console")
        self._console.setReadOnly(True)
        self._console.setMaximumBlockCount(MAX_LOG_BLOCKS)
        self._console.setMinimumHeight(150)
        self._console.setFrameShape(QFrame.NoFrame)
        self._console.setPlaceholderText("Connect a port to see its traffic here.")
        card_layout.addWidget(self._console)

        return card

    def apply_base_style(self, theme_name="dark"):
        super().apply_base_style(theme_name)
        is_light = theme_name.lower() == "light"
        colors = CARD_COLORS[is_light]
        if hasattr(self, "_empty_hint"):
            self._empty_hint.setStyleSheet(
                f"font-size: 12px; color: {colors['muted']}; background: transparent;"
            )
        if hasattr(self, "_summary"):
            self._summary.setStyleSheet(
                f"font-size: 11px; color: {colors['muted']}; background: transparent;"
            )
        if hasattr(self, "_console_title"):
            self._console_title.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {colors['muted']}; "
                "background: transparent;"
            )
        if hasattr(self, "_console"):
            # QPlainTextEdit is not themed by BasePage (only QTextEdit is).
            # NOTE: every brace must be doubled inside an f-string, otherwise
            # Qt rejects the whole stylesheet.
            self._console.setStyleSheet(
                f"QPlainTextEdit#serial_console {{ background-color: {colors['bg']}; "
                f"border: 1px solid {colors['border']}; border-radius: 8px; "
                f"color: {colors['log_text']}; padding: 6px; "
                "selection-background-color: #568af2; }"
            )
        card = self.findChild(QFrame, "serial_console_card")
        if card is not None:
            card.setStyleSheet(
                f"#serial_console_card {{ background-color: {colors['bg']}; "
                f"border: 1px solid {colors['border']}; border-radius: 10px; }}"
            )
        for row in getattr(self, "_rows", {}).values():
            row.apply_theme(is_light)

    # ------------------------------------------------------------------
    # Port list
    # ------------------------------------------------------------------

    @staticmethod
    def _port_sort_key(name: str):
        return [int(part) if part.isdigit() else part.lower()
                for part in re.split(r"(\d+)", name)]

    @Slot()
    def _refresh_ports(self):
        """Refresh button: request an immediate scan (starts the thread if needed)."""
        if self._scanner.isRunning():
            self._scanner.request_scan()
        else:
            self._scanner.start()

    @Slot(list)
    def _on_ports_found(self, ports):
        self._apply_ports(dict(ports))

    @Slot(str)
    def _on_scan_failed(self, message: str):
        self.show_warning("Serial Port", f"Port scan failed: {message}")

    def _apply_ports(self, detected: dict):
        is_light = self._get_current_theme().lower() == "light"

        # Drop rows whose device is gone and which are not open.
        for name in list(self._rows.keys()):
            if name in detected:
                self._rows[name].set_detected(True, detected[name])
                continue
            if name in self._open_ports:
                self._rows[name].set_detected(False)
                continue
            row = self._rows.pop(name)
            self._rows_layout.removeWidget(row)
            row.deleteLater()

        # Add rows for newly detected ports.
        for name in sorted(detected.keys(), key=self._port_sort_key):
            if name in self._rows:
                continue
            baud = self._baud_prefs.get(name, DEFAULT_BAUDRATE)
            row = SerialPortRow(name, detected[name], COMMON_BAUDRATES, baud, is_light, self)
            row.connect_requested.connect(self._open_port)
            row.disconnect_requested.connect(self._close_port)
            self._rows[name] = row

        self._reorder_rows()
        self._update_empty_state()

    def _reorder_rows(self):
        for row in self._rows.values():
            self._rows_layout.removeWidget(row)
        for name in sorted(self._rows.keys(), key=self._port_sort_key):
            self._rows_layout.addWidget(self._rows[name])

    def _update_empty_state(self):
        self._empty_hint.setVisible(not self._rows)
        if self._rows:
            self._summary.setText(
                f"{len(self._open_ports)} connected · {len(self._rows)} detected"
            )
        else:
            self._summary.setText("")

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def _connect_manager_signals(self):
        self.serial_manager.port_closed.connect(self._on_port_closed)
        self.serial_manager.connection_lost.connect(self._on_connection_lost)
        self.serial_manager.error_occurred.connect(self._on_error_occurred)
        self.serial_manager.data_received.connect(self._on_data_received)

    @Slot(str)
    def _open_port(self, port_name: str):
        row = self._rows.get(port_name)
        if row is None:
            return

        baudrate = row.baudrate()
        self._baud_prefs[port_name] = baudrate
        row.baud_combo.setEditText(str(baudrate))

        success, port_id, error = self.serial_manager.open_port(
            SerialConfig(port=port_name, baudrate=baudrate)
        )
        if not success:
            row.set_disconnected("error")
            self.show_error("Serial Port", error or f"Failed to open {port_name}")
            return

        self._open_ports[port_name] = port_id
        row.set_connected(port_id)
        self._update_empty_state()
        self._sync_console_target()
        self.show_success("Serial Port", f"{port_name} opened at {baudrate} baud")

    @Slot(str)
    def _close_port(self, port_name: str):
        port_id = self._open_ports.pop(port_name, None)
        if port_id is None:
            return
        self.serial_manager.close_port(port_id)
        row = self._rows.get(port_name)
        if row is not None:
            row.set_disconnected("off")
        self._update_empty_state()
        self._sync_console_target()
        self.show_info("Serial Port", f"{port_name} closed")

    @Slot(str)
    def _on_port_closed(self, port_id: str):
        for name, pid in list(self._open_ports.items()):
            if pid == port_id:
                del self._open_ports[name]
                row = self._rows.get(name)
                if row is not None:
                    row.set_disconnected("off")
        self._update_empty_state()
        self._sync_console_target()

    @Slot(str, str)
    def _on_connection_lost(self, port_id: str, error_msg: str):
        # A lost connection is an abnormal close: release the handle.
        for name, pid in list(self._open_ports.items()):
            if pid != port_id:
                continue
            del self._open_ports[name]
            self.serial_manager.close_port(port_id)
            row = self._rows.get(name)
            if row is not None:
                row.set_disconnected("error")
            self.show_error("Serial Port", f"{name}: {error_msg}")
        self._update_empty_state()
        self._sync_console_target()

    @Slot(str, str)
    def _on_error_occurred(self, port_id: str, error_msg: str):
        for name, pid in self._open_ports.items():
            if pid == port_id:
                self.show_error("Serial Port", f"{name}: {error_msg}")
                break

    # ------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------

    def _primary_port(self):
        """Return ``(name, port_id)`` of the first connected port, if any."""
        for name, port_id in self._open_ports.items():
            return name, port_id
        return None, None

    def _sync_console_target(self):
        """Point the console at the first connected port (or clear it)."""
        name, port_id = self._primary_port()
        if port_id == self._log_port_id:
            return

        self._log_port_id = port_id
        if port_id is None:
            self._console_title.setText("Console")
            return

        config = self.serial_manager.get_connection_info(port_id)
        baud = config.baudrate if config else DEFAULT_BAUDRATE
        self._console_title.setText(f"Console — {name} @ {baud}")
        self._append_log(f"--- {name} @ {baud} 8N1 ---")

    @Slot(str, bytes)
    def _on_data_received(self, port_id: str, data: bytes):
        if port_id != self._log_port_id or not data:
            return
        self._append_frame(data)

    def _on_view_mode_changed(self, _checked: bool):
        mode = "HEX" if self._hex_view.isChecked() else "TEXT"
        self._console.appendPlainText(f"--- view mode: {mode} ---")

    @staticmethod
    def _to_hex(data: bytes) -> str:
        return " ".join(f"{byte:02X}" for byte in data)

    def _render_frame(self, data: bytes) -> str:
        """Render one received frame without losing or merging any byte."""
        if self._hex_view.isChecked():
            return f"RX {len(data)}B: {self._to_hex(data)}"

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            # Not decodable as text: bytes are the only faithful view.
            return f"RX {len(data)}B: {self._to_hex(data)}"

        # A frame made only of whitespace / line breaks would render as blank
        # lines, so show its bytes instead of an apparently empty log entry.
        if text.strip() == "":
            return f"RX {len(data)}B: {self._to_hex(data)}"

        # CRLF becomes one line break; lone CR/LF also break the line. Repeated
        # newlines are preserved so nothing is silently merged, and every other
        # control character is escaped so it stays visible.
        out = []
        index = 0
        while index < len(text):
            ch = text[index]
            if ch == "\r":
                out.append("\n")
                if index + 1 < len(text) and text[index + 1] == "\n":
                    index += 2
                    continue
            elif ch == "\n":
                out.append("\n")
            elif ch == "\t":
                out.append("    ")
            elif ch.isprintable():
                out.append(ch)
            else:
                out.append(f"\\x{ord(ch):02X}")
            index += 1
        return "".join(out)

    def _append_frame(self, data: bytes):
        stamp = time.strftime("%H:%M:%S")
        rendered = self._render_frame(data)
        # splitlines() drops the trailing empty segment produced by a final CRLF.
        for line in rendered.splitlines() or [""]:
            self._console.appendPlainText(f"[{stamp}] {line}")

    def _append_log(self, text: str):
        stamp = time.strftime("%H:%M:%S")
        self._console.appendPlainText(f"[{stamp}] {text}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        if not self._scanner.isRunning():
            self._scanner.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        # Stop polling only — open connections must survive navigation.
        self._scanner.stop()
