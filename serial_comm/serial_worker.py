# -*- coding: utf-8 -*-
"""Serial port worker thread for reading data.

Data is delivered as *raw frames*: bytes are never split on ``\\r``/``\\n`` and
never stripped, so payloads containing 0x0A / 0x0D (single or combined) reach
the UI byte-for-byte. Framing is purely time based — bytes that arrive close
together are grouped, which keeps a binary frame intact without interpreting
its content.
"""

import time

from PySide6.QtCore import QThread, Signal

# Frames are read in bounded chunks so a flooding device cannot starve the
# event loop, balloon memory, or produce a single unreadable 100 KB log line.
MAX_FRAME_BYTES = 4096
# How long to keep collecting bytes before emitting a frame.
FRAME_GAP = 0.012
# Hard cap on frame assembly so a continuously streaming device still yields
# data instead of being merged into one ever-growing frame.
FRAME_MAX = 0.05


class SerialWorker(QThread):
    """Worker thread for reading serial port data without blocking UI."""

    data_received = Signal(bytes)
    connection_lost = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, serial_port, parent=None):
        super().__init__(parent)
        self.serial_port = serial_port
        self.running = False

    def run(self):
        """Read raw frames until stopped or the port disappears."""
        self.running = True
        port = self.serial_port

        try:
            while self.running and port is not None and port.is_open:
                # Blocking read (up to the port timeout) instead of waking the
                # CPU 200 times/second while the line is idle.
                try:
                    waiting = port.in_waiting
                    frame = bytearray(port.read(min(waiting, MAX_FRAME_BYTES) or 1))
                except Exception as exc:
                    # Device unplugged / handle invalidated: abnormal close.
                    self.connection_lost.emit(str(exc))
                    break

                if not frame or not self.running:
                    continue

                # Gather the rest of a burst so a logical frame is not split
                # across signals. This never inspects the byte values.
                frame_started = time.monotonic()
                deadline = frame_started + FRAME_GAP
                while (self.running and len(frame) < MAX_FRAME_BYTES
                       and time.monotonic() < deadline):
                    try:
                        extra_waiting = port.in_waiting
                    except Exception as exc:
                        self.connection_lost.emit(str(exc))
                        self.running = False
                        break
                    if not extra_waiting:
                        QThread.usleep(2000)
                        continue
                    try:
                        frame.extend(port.read(min(extra_waiting, MAX_FRAME_BYTES - len(frame))))
                    except Exception as exc:
                        self.connection_lost.emit(str(exc))
                        self.running = False
                        break
                    # Bounded assembly: never starve the consumer during a stream.
                    deadline = min(time.monotonic() + FRAME_GAP, frame_started + FRAME_MAX)

                if frame and self.running:
                    # Emit the frame untouched: 0x0A / 0x0D are data, not framing.
                    self.data_received.emit(bytes(frame))
        except Exception as exc:
            # Windows raises OSError (WinError 8/1450) from wait primitives when
            # the process runs out of kernel resources. Never let it escape
            # ``run()``: the thread would die while the UI still shows "open".
            self.running = False
            self.connection_lost.emit(f"Serial reader stopped: {exc}")
            return

        # The loop can only fall through while ``running`` is still True if the
        # handle went away underneath us (device removed, port closed by
        # another process). Report it so the UI can drop the connection.
        if self.running:
            self.running = False
            self.connection_lost.emit("Port closed unexpectedly")

    def stop(self):
        """Stop the worker thread."""
        self.running = False
        if not self.wait(1500) and self.isRunning():
            self.terminate()
            self.wait(500)
