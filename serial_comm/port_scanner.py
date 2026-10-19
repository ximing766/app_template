# -*- coding: utf-8 -*-
"""Background port scanner.

``serial.tools.list_ports.comports()`` enumerates the OS device registry and
can take tens of milliseconds; running it on the GUI thread every couple of
seconds would cause visible jank. This thread scans on an interval and emits
the result to the UI thread via a queued signal.
"""

from PySide6.QtCore import QCoreApplication, QThread, Signal

from .port_utils import list_serial_ports


class PortScanner(QThread):
    """Periodically scans for available serial ports."""

    ports_found = Signal(list)   # list[tuple[str, str]] -> (device, description)
    scan_failed = Signal(str)

    def __init__(self, interval_ms: int = 2000, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self._running = False
        self._scan_now = False

        # Guarantee the thread is stopped before the process tears down.
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop)

    def request_scan(self):
        """Ask the thread to scan again immediately."""
        self._scan_now = True

    def run(self):
        self._running = True
        while self._running:
            try:
                ports = list_serial_ports()
            except Exception as exc:  # never let the thread die on a bad driver
                self.scan_failed.emit(str(exc))
                ports = []

            if not self._running:
                break

            self.ports_found.emit(ports)

            self._scan_now = False
            waited = 0
            while self._running and not self._scan_now and waited < self.interval_ms:
                self.msleep(100)
                waited += 100

    def stop(self):
        """Stop the scan loop and wait for the thread to finish."""
        self._running = False
        self.wait(2000)
