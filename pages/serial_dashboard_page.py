from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QSplitter, QSizePolicy
from qfluentwidgets import (ComboBox, PushButton, LineEdit, TextEdit, ToolButton, CheckBox,
                           StrongBodyLabel, CaptionLabel, FluentIcon as FIF,
                           CardWidget, SimpleCardWidget, InfoBar, ScrollArea)
from PyQt6.QtCore import Qt, QTimer, QIODevice, QPointF, QRectF, QRegularExpression, QThread, pyqtSignal, QDateTime, QUrl
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPolygonF, QRegularExpressionValidator, QDesktopServices, QAction
from pages import BasePage
from core.simple_logger import SimpleLogger
import math
import re
import time
import os

class SerialConfigWidget(CardWidget):
    line_received = pyqtSignal(str) # Signal for external parsers (emits decoded string)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.serial = QSerialPort()
        # self.read_thread = None # Removed threading to fix crash
        self.logger = SimpleLogger()
        self.log_file_path = None
        
        # Data buffers
        self.received_lines = [] # List of bytes objects for re-rendering
        self.max_lines = 10000
        self.serial_buffer = bytearray()
        self.split_on_newline = True
        self._last_buffer_update_ts = 0.0
        
        # Timer for idle flush
        self.flush_timer = QTimer(self)
        self.flush_timer.setInterval(100)
        self.flush_timer.timeout.connect(self.check_flush_buffer)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        
        self.port_combo = ComboBox()
        self.port_combo.setMaximumWidth(120)
        self.refresh_ports()
        grid.addWidget(self.port_combo, 0, 0)
        
        self.baud_combo = ComboBox()
        self.baud_combo.setMaximumWidth(120)
        self.baud_combo.addItems(['9600', '115200', '230400', '460800', '921600', '1000000', '3000000'])
        self.baud_combo.setCurrentText('3000000')
        grid.addWidget(self.baud_combo, 0, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(3000)
        self.refresh_timer.timeout.connect(self.refresh_ports)
        self.refresh_timer.start()

        self.btn_open = ToolButton(FIF.PLAY)
        self.btn_open.clicked.connect(self.toggle_serial)
        grid.addWidget(self.btn_open, 0, 2)

        self.btn_clear = ToolButton(FIF.DELETE)
        self.btn_clear.clicked.connect(self.clear_log)
        grid.addWidget(self.btn_clear, 0, 3)
        
        spacer = QWidget()          # 纯占位，不显示任何东西
        grid.addWidget(spacer, 0, 4)
        grid.setColumnStretch(4, 1) # 只让第 4 列弹性扩展

        self.btn_hex_rec = CheckBox("HEX")
        self.btn_hex_rec.clicked.connect(self.toggle_hex_rec_mode)
        grid.addWidget(self.btn_hex_rec, 0, 5)
        
        self.chk_timestamp = CheckBox("TIME")
        self.chk_timestamp.setToolTip("显示时间戳")
        self.chk_timestamp.setChecked(False)
        grid.addWidget(self.chk_timestamp, 0, 6)
        
        self.chk_autoscroll = CheckBox("AUTO")
        self.chk_autoscroll.setToolTip("自动滚动")
        self.chk_autoscroll.setChecked(True)
        grid.addWidget(self.chk_autoscroll, 0, 7)   

        self.btn_open_log = ToolButton(FIF.DOCUMENT)
        self.btn_open_log.setFixedWidth(40)
        self.btn_open_log.setToolTip("打开当前日志文件")
        self.btn_open_log.clicked.connect(self.open_current_log)
        self.btn_open_log.setEnabled(False)
        grid.addWidget(self.btn_open_log, 0, 8)
        
        self.btn_open_folder = ToolButton(FIF.FOLDER)
        self.btn_open_folder.setFixedWidth(40)
        self.btn_open_folder.setToolTip("打开日志文件夹")
        self.btn_open_folder.clicked.connect(self.open_log_folder)
        grid.addWidget(self.btn_open_folder, 0, 9)
        

        send_layout = QHBoxLayout()
        self.send_edit = LineEdit()
        self.send_edit.setText("rssi:-55 or dist:150")
        self.send_edit.setPlaceholderText("发送指令...")
        self.btn_send = ToolButton(FIF.SEND)
        self.btn_send.clicked.connect(self.send_data)
        self.btn_hex = CheckBox("HEX")
        self.btn_hex.clicked.connect(self.toggle_hex_send_mode)
        
        send_layout.addWidget(self.btn_hex)
        send_layout.addWidget(self.send_edit)
        send_layout.addWidget(self.btn_send)
        
        self.log_area = TextEdit()
        self.log_area.setPlaceholderText("接收数据...")
        self.log_area.setReadOnly(True)
        # Set max block count to avoid memory issues (slightly more than max_lines to allow buffer)
        self.log_area.document().setMaximumBlockCount(self.max_lines + 100)
        self.log_area.setFont(QFont("Microsoft YaHei", 12))

        layout.addLayout(grid)
        layout.addWidget(self.log_area, 1)
        layout.addLayout(send_layout)
        
    def refresh_ports(self):
        current = self.port_combo.currentText()
        ports = [p.portName() for p in QSerialPortInfo.availablePorts()]
        self.port_combo.clear()
        for name in ports:
            self.port_combo.addItem(name)
        if current and current in ports:
            ix = ports.index(current)
            self.port_combo.setCurrentIndex(ix)
            
    def toggle_serial(self):
        if self.serial.isOpen():
            # Disconnect signals first to avoid pending events
            try:
                self.serial.readyRead.disconnect(self.on_ready_read)
            except: pass
            
            self.serial.close()
            self.flush_timer.stop()
            
            self.btn_open.setIcon(FIF.PLAY)
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.log_area.append(">>> 串口已关闭")
        else:
            port_name = self.port_combo.currentText()
            if not port_name:
                return
                
            self.serial.setPortName(port_name)
            self.serial.setBaudRate(int(self.baud_combo.currentText()))
            
            if self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
                self.btn_open.setIcon(FIF.PAUSE)
                self.port_combo.setEnabled(False)
                self.baud_combo.setEnabled(False)
                self.log_area.append(f">>> 串口 {port_name} 已打开")
                
                # Start logging
                self.log_file_path = self.logger.start_logging(prefix=f"{port_name}")
                self.btn_open_log.setEnabled(True)
                
                # Setup Async Read
                self.serial.readyRead.connect(self.on_ready_read)
                self.serial.errorOccurred.connect(self.handle_serial_error)
                
                # Sync split mode
                self.split_on_newline = not self.btn_hex_rec.isChecked()
                self.serial_buffer.clear()
                self.flush_timer.start()
            else:
                self.log_area.append(f"无法打开串口 {port_name}")

    def on_ready_read(self):
        while self.serial.bytesAvailable():
            data = self.serial.readAll().data()
            if not data: continue
            
            if self.split_on_newline:
                self.serial_buffer.extend(data)
                self._last_buffer_update_ts = time.time()
                
                # Safety limit to prevent memory exhaustion
                if len(self.serial_buffer) > 1024 * 1024:
                     self.serial_buffer = self.serial_buffer[-1024:]
                     
                while True:
                    pos_n = self.serial_buffer.find(b"\n")
                    pos_r = self.serial_buffer.find(b"\r")
                    positions = [p for p in (pos_n, pos_r) if p != -1]
                    if not positions: break
                    
                    line_end = min(positions)
                    line = bytes(self.serial_buffer[:line_end + 1])
                    self.serial_buffer = self.serial_buffer[line_end + 1:]
                    
                    if line.strip():
                        self.handle_data_received(line)
            else:
                self.handle_data_received(data)

    def check_flush_buffer(self):
        if self.split_on_newline and self.serial_buffer:
             now = time.time()
             if now - self._last_buffer_update_ts >= 0.2:
                 line = bytes(self.serial_buffer)
                 self.serial_buffer.clear()
                 if line.strip():
                     self.handle_data_received(line)

    def handle_serial_error(self, error):
        if error == QSerialPort.SerialPortError.NoError: return
        # Don't log if closed cleanly (ResourceError often happens on close/unplug)
        if not self.serial.isOpen() and error == QSerialPort.SerialPortError.ResourceError:
            return
            
        self.log_area.append(f">>> 串口错误: {self.serial.errorString()}")
        if self.serial.isOpen() and error != QSerialPort.SerialPortError.NoError:
             self.toggle_serial()

    def handle_data_received(self, data: bytes):
        # 1. Save raw bytes to buffer
        self.received_lines.append(data)
        if len(self.received_lines) > self.max_lines:
            self.received_lines.pop(0)
            
        # 2. Format for display
        hex_mode = self.btn_hex_rec.isChecked()
        timestamp = self.chk_timestamp.isChecked()
        
        display_text = ""
        if hex_mode:
            display_text = " ".join([f"{b:02X}" for b in data])
        else:
            display_text = data.decode('utf-8', errors='replace').strip()
            
        if not display_text:
            return

        if timestamp:
            time_str = QDateTime.currentDateTime().toString("HH:mm:ss.zzz")
            display_text = f"[{time_str}] {display_text}"
            
        sb = self.log_area.verticalScrollBar()
        prev_val = None
        if not self.chk_autoscroll.isChecked():
            prev_val = sb.value()

        self.log_area.append(display_text)
        
        # 3. Auto Scroll
        if self.chk_autoscroll.isChecked():
            sb.setValue(sb.maximum())
        elif prev_val is not None:
            sb.setValue(prev_val)
            
        self.logger.log(display_text + "\n")
        
        # 5. Emit signal for external parsers (Try to decode as str)
        try:
            str_data = data.decode('utf-8', errors='ignore')
            self.line_received.emit(str_data)
        except:
            pass

    def send_data(self):
        if self.serial.isOpen():
            text = self.send_edit.text() # Don't strip, allow sending spaces/newlines if intended
            if not text: return
            
            try:
                if self.btn_hex.isChecked():
                    # Remove spaces for hex conversion
                    clean_hex = text.replace(" ", "")
                    data = bytes.fromhex(clean_hex)
                else:
                    data = text.encode('utf-8')
                
                self.serial.write(data)
                
            except ValueError:
                InfoBar.error("发送失败", "无效的HEX格式", parent=self)
                return
            except Exception as e:
                InfoBar.error("发送失败", str(e), parent=self)

    def toggle_hex_send_mode(self):
        if self.btn_hex.isChecked():
            self.send_edit.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9A-Fa-f\\s]*")))
            self.send_edit.setPlaceholderText("发送HEX指令 (例: AA BB)...")
        else:
            self.send_edit.setValidator(None)
            self.send_edit.setPlaceholderText("发送指令...")
    
    def toggle_hex_rec_mode(self):
        # Switch split mode
        is_hex = self.btn_hex_rec.isChecked()
        self.split_on_newline = not is_hex
            
        self.log_area.clear()
        timestamp = self.chk_timestamp.isChecked()
        
        sb = []
        for data in self.received_lines:
            if is_hex:
                txt = " ".join([f"{b:02X}" for b in data])
            else:
                txt = data.decode('utf-8', errors='replace').strip()
            if not txt: continue
            if timestamp:
                pass 
            sb.append(txt)
            
        # Optimization: batch append
        if len(sb) > 1000:
            sb = sb[-1000:] # Only show last 1000 on toggle to be fast
            
        self.log_area.setPlainText("\n".join(sb))
        
        if self.chk_autoscroll.isChecked():
            self.log_area.verticalScrollBar().setValue(
                self.log_area.verticalScrollBar().maximum()
            )

    def clear_log(self):
        self.log_area.clear()
        self.received_lines.clear()
        
    def open_log_folder(self):
        path = self.logger.get_log_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        
    def open_current_log(self):
        path = self.logger.get_current_log_file()
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            InfoBar.warning("提示", "当前没有正在记录的日志文件", parent=self)

class SerialDashboardPage(BasePage):
    def __init__(self, parent=None):
        self.cards = []
        self.grid = None
        super().__init__("serial_dashboard", parent)

    def init_content(self):
        root = QVBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        btn_add = ToolButton(FIF.ADD)
        btn_del = ToolButton(FIF.REMOVE)
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
            InfoBar.warning("提示", "最多显示4个串口卡片", parent=self)
            return
        card = SerialConfigWidget("Serial")
        self.cards.append(card)
        self.relayout()

    def remove_card(self):
        if not self.cards:
            return
        if len(self.cards) == 1:
            InfoBar.warning("提示", "至少保留一个串口卡片", parent=self)
            return
        card = self.cards.pop()
        card.setParent(None)
        self.relayout()

    def build_splitter(self):
        n = len(self.cards)
        if n == 1:
            return self.cards[0]
        if n == 2:
            s = QSplitter(Qt.Orientation.Horizontal)
            s.addWidget(self.cards[0])
            s.addWidget(self.cards[1])
            s.setChildrenCollapsible(False)
            s.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            s.setStretchFactor(0, 1)
            s.setStretchFactor(1, 1)
            return s
        if n == 3:
            top = QSplitter(Qt.Orientation.Horizontal)
            top.addWidget(self.cards[0])
            top.addWidget(self.cards[1])
            top.setChildrenCollapsible(False)
            top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            top.setStretchFactor(0, 1)
            top.setStretchFactor(1, 1)
            root = QSplitter(Qt.Orientation.Vertical)
            root.addWidget(top)
            root.addWidget(self.cards[2])
            root.setChildrenCollapsible(False)
            root.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            root.setStretchFactor(0, 1)
            root.setStretchFactor(1, 1)
            return root
        if n == 4:
            top = QSplitter(Qt.Orientation.Horizontal)
            top.addWidget(self.cards[0])
            top.addWidget(self.cards[1])
            top.setChildrenCollapsible(False)
            top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            top.setStretchFactor(0, 1)
            top.setStretchFactor(1, 1)
            bottom = QSplitter(Qt.Orientation.Horizontal)
            bottom.addWidget(self.cards[2])
            bottom.addWidget(self.cards[3])
            bottom.setChildrenCollapsible(False)
            bottom.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            bottom.setStretchFactor(0, 1)
            bottom.setStretchFactor(1, 1)
            root = QSplitter(Qt.Orientation.Vertical)
            root.addWidget(top)
            root.addWidget(bottom)
            root.setChildrenCollapsible(False)
            root.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            root.setStretchFactor(0, 1)
            root.setStretchFactor(1, 1)
            return root
        return QWidget()

    def relayout(self):
        # 1) Detach cards first to avoid being deleted with parent splitters
        for c in list(self.cards):
            if c is not None:
                c.setParent(None)
        # 2) Clear container layout (remove old splitters and widgets without deleting)
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        # 3) Reset current splitter if exists (do not delete)
        if self.current_splitter:
            self.current_splitter.setParent(None)
            self.current_splitter = None
        w = self.build_splitter()
        if isinstance(w, QSplitter):
            self.current_splitter = w
            self.container_layout.addWidget(w)
        else:
            self.container_layout.addWidget(w)
