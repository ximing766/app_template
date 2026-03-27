from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, 
                               QSplitter, QSizePolicy, QComboBox, QPushButton, 
                               QLineEdit, QTextEdit, QCheckBox, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QIODevice, Signal, QDateTime, QUrl
from PySide6.QtGui import QFont, QRegularExpressionValidator, QDesktopServices, QIcon
from pages.base_page import BasePage
from core.simple_logger import SimpleLogger
import time
import os

from gui.widgets.py_icon_button.py_icon_button import PyIconButton
from gui.core.functions import Functions

class SerialConfigWidget(QFrame):
    line_received = Signal(str) 

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("SerialConfigWidget")
        self.setStyleSheet("""
            #SerialConfigWidget {
                background-color: transparent;
                border-radius: 8px;
                border: 1px solid #3f444e;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.serial = QSerialPort()
        self.logger = SimpleLogger()
        self.log_file_path = None
        
        # Data buffers
        self.received_lines = [] 
        self.max_lines = 10000
        self.serial_buffer = bytearray()
        self.split_on_newline = True
        self._last_buffer_update_ts = 0.0
        
        # Timer for idle flush
        self.flush_timer = QTimer(self)
        self.flush_timer.setInterval(100)
        self.flush_timer.timeout.connect(self.check_flush_buffer)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        
        self.port_combo = QComboBox()
        self.port_combo.setMaximumWidth(120)
        self.port_combo.setMinimumHeight(30)
        self.refresh_ports()
        grid.addWidget(self.port_combo, 0, 0)
        
        self.baud_combo = QComboBox()
        self.baud_combo.setMaximumWidth(120)
        self.baud_combo.setMinimumHeight(30)
        self.baud_combo.addItems(['9600', '115200', '230400', '460800', '921600', '1000000', '3000000'])
        self.baud_combo.setCurrentText('3000000')
        grid.addWidget(self.baud_combo, 0, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(3000)
        self.refresh_timer.timeout.connect(self.refresh_ports)
        self.refresh_timer.start()

        self.btn_open = QPushButton("Open")
        self.btn_open.setMinimumHeight(30)
        self.btn_open.clicked.connect(self.toggle_serial)
        grid.addWidget(self.btn_open, 0, 2)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setMinimumHeight(30)
        self.btn_clear.clicked.connect(self.clear_log)
        grid.addWidget(self.btn_clear, 0, 3)
        
        spacer = QWidget()          
        grid.addWidget(spacer, 0, 4)
        grid.setColumnStretch(4, 1) 

        self.btn_hex_rec = QCheckBox("HEX")
        self.btn_hex_rec.clicked.connect(self.toggle_hex_rec_mode)
        grid.addWidget(self.btn_hex_rec, 0, 5)
        
        self.chk_timestamp = QCheckBox("TIME")
        self.chk_timestamp.setToolTip("Show timestamp")
        self.chk_timestamp.setChecked(False)
        grid.addWidget(self.chk_timestamp, 0, 6)
        
        self.chk_autoscroll = QCheckBox("PIN")
        self.chk_autoscroll.setToolTip("Auto scroll")
        self.chk_autoscroll.setChecked(True)
        grid.addWidget(self.chk_autoscroll, 0, 7)   

        self.btn_open_log = QPushButton("Log")
        self.btn_open_log.setMinimumHeight(30)
        self.btn_open_log.clicked.connect(self.open_current_log)
        self.btn_open_log.setEnabled(False)
        grid.addWidget(self.btn_open_log, 0, 8)
        
        self.btn_open_folder = QPushButton("Folder")
        self.btn_open_folder.setMinimumHeight(30)
        self.btn_open_folder.clicked.connect(self.open_log_folder)
        grid.addWidget(self.btn_open_folder, 0, 9)

        send_layout = QHBoxLayout()
        self.send_edit = QLineEdit()
        self.send_edit.setMinimumHeight(30)
        self.send_edit.setText("rssi:-55 or dist:150")
        self.send_edit.setPlaceholderText("Send command...")
        
        self.btn_send = QPushButton("Send")
        self.btn_send.setMinimumHeight(30)
        self.btn_send.clicked.connect(self.send_data)
        
        self.btn_hex = QCheckBox("HEX")
        self.btn_hex.clicked.connect(self.toggle_hex_send_mode)
        
        send_layout.addWidget(self.btn_hex)
        send_layout.addWidget(self.send_edit)
        send_layout.addWidget(self.btn_send)
        
        self.log_area = QTextEdit()
        self.log_area.setPlaceholderText("Received data...")
        self.log_area.setReadOnly(True)
        self.log_area.document().setMaximumBlockCount(self.max_lines + 100)
        self.log_area.setFont(QFont("Consolas", 11))

        layout.addLayout(grid)
        layout.addWidget(self.log_area, 1)
        layout.addLayout(send_layout)

        self.serial.readyRead.connect(self.receive_data)

    def refresh_ports(self):
        current_port = self.port_combo.currentText()
        ports = QSerialPortInfo.availablePorts()
        self.port_combo.clear()
        for port in ports:
            self.port_combo.addItem(port.portName())
        if current_port:
            index = self.port_combo.findText(current_port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

    def toggle_serial(self):
        if self.serial.isOpen():
            self.serial.close()
            self.btn_open.setText("Open")
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.log_area.append(">>> Serial closed")
            
            # Stop logging
            self.log_file_path = None
            self.btn_open_log.setEnabled(False)
        else:
            port_name = self.port_combo.currentText()
            if not port_name:
                return
                
            self.serial.setPortName(port_name)
            self.serial.setBaudRate(int(self.baud_combo.currentText()))
            
            if self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
                self.btn_open.setText("Close")
                self.port_combo.setEnabled(False)
                self.baud_combo.setEnabled(False)
                self.log_area.append(f">>> Serial {port_name} opened")
                
                # Start logging
                self.log_file_path = self.logger.start_logging(f"serial_{port_name}")
                self.btn_open_log.setEnabled(True)

    def toggle_hex_rec_mode(self):
        self.split_on_newline = not self.btn_hex_rec.isChecked()

    def toggle_hex_send_mode(self):
        pass

    def send_data(self):
        if not self.serial.isOpen():
            self.show_warning("Error", "Serial port is not open")
            return
            
        data = self.send_edit.text()
        if not data:
            return
            
        try:
            if self.btn_hex.isChecked():
                # Remove spaces and convert to bytes
                data = data.replace(" ", "")
                byte_data = bytes.fromhex(data)
                self.serial.write(byte_data)
            else:
                self.serial.write((data + "\r\n").encode('utf-8'))
        except Exception as e:
            self.show_warning("Error", str(e))

    def receive_data(self):
        data = self.serial.readAll()
        if data:
            self.serial_buffer.extend(data)
            self._last_buffer_update_ts = time.time()
            if not self.flush_timer.isActive():
                self.flush_timer.start()

    def check_flush_buffer(self):
        # Process data in chunks
        if not self.serial_buffer:
            self.flush_timer.stop()
            return
            
        # If it's been quiet for a bit, or buffer is getting large, process it
        if time.time() - self._last_buffer_update_ts > 0.05 or len(self.serial_buffer) > 1024:
            self.process_buffer()

    def process_buffer(self):
        if not self.serial_buffer:
            return
            
        if self.btn_hex_rec.isChecked():
            # Hex mode
            hex_str = self.serial_buffer.hex(' ').upper()
            self.append_log(hex_str)
            self.serial_buffer.clear()
        else:
            # Text mode - process complete lines
            while True:
                # Find newline
                nl_idx = self.serial_buffer.find(b'\n')
                if nl_idx == -1:
                    break
                    
                line_data = self.serial_buffer[:nl_idx+1]
                self.serial_buffer = self.serial_buffer[nl_idx+1:]
                
                try:
                    text = line_data.decode('utf-8', errors='replace').strip()
                    if text:
                        self.append_log(text)
                        self.line_received.emit(text)
                except Exception:
                    pass

    def append_log(self, text):
        if self.chk_timestamp.isChecked():
            ts = QDateTime.currentDateTime().toString("HH:mm:ss.zzz")
            text = f"[{ts}] {text}"
            
        self.log_area.append(text)
        
        # Write to file if open
        if self.log_file_path:
            self.logger.log(text + "\n")
        
        if self.chk_autoscroll.isChecked():
            vsb = self.log_area.verticalScrollBar()
            vsb.setValue(vsb.maximum())

    def clear_log(self):
        self.log_area.clear()

    def open_current_log(self):
        if self.log_file_path and os.path.exists(self.log_file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.log_file_path))

    def open_log_folder(self):
        folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        if os.path.exists(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class SerialDashboardPage(BasePage):
    def __init__(self, parent=None):
        self.cards = []
        self.grid = None
        super().__init__("serial", parent)

    def init_content(self):
        self.apply_base_style()
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("+")
        btn_del = QPushButton("-")
        btn_add.clicked.connect(self.add_card)
        btn_del.clicked.connect(self.remove_card)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_del)
        toolbar.addStretch(1)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.current_splitter = None

        root.addLayout(toolbar)
        root.addWidget(self.container, 1)
        self.layout.addLayout(root)

        self.add_card()

    def add_card(self):
        if len(self.cards) >= 4:
            self.show_warning("Warning", "Maximum 4 serial cards allowed")
            return
        card = SerialConfigWidget(f"Serial {len(self.cards) + 1}")
        self.cards.append(card)
        self.relayout()

    def remove_card(self):
        if not self.cards:
            return
        if len(self.cards) == 1:
            self.show_warning("Warning", "At least 1 serial card must be kept")
            return
            
        card = self.cards.pop()
        card.deleteLater()
        self.relayout()

    def relayout(self):
        if self.current_splitter:
            self.container_layout.removeWidget(self.current_splitter)
            self.current_splitter.deleteLater()

        count = len(self.cards)
        if count == 0:
            return

        if count == 1:
            self.current_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.current_splitter.addWidget(self.cards[0])
            
        elif count == 2:
            self.current_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.current_splitter.addWidget(self.cards[0])
            self.current_splitter.addWidget(self.cards[1])
            
        elif count == 3:
            self.current_splitter = QSplitter(Qt.Orientation.Vertical)
            top = QSplitter(Qt.Orientation.Horizontal)
            top.addWidget(self.cards[0])
            top.addWidget(self.cards[1])
            self.current_splitter.addWidget(top)
            self.current_splitter.addWidget(self.cards[2])
            
        elif count == 4:
            self.current_splitter = QSplitter(Qt.Orientation.Vertical)
            top = QSplitter(Qt.Orientation.Horizontal)
            top.addWidget(self.cards[0])
            top.addWidget(self.cards[1])
            bottom = QSplitter(Qt.Orientation.Horizontal)
            bottom.addWidget(self.cards[2])
            bottom.addWidget(self.cards[3])
            self.current_splitter.addWidget(top)
            self.current_splitter.addWidget(bottom)

        if self.current_splitter:
            self.container_layout.addWidget(self.current_splitter)
            # Re-apply base style to ensure splitter style is applied to new instances
            self.apply_base_style()