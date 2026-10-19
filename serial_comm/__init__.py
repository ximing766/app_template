# -*- coding: utf-8 -*-
"""Serial communication module for production testing."""

from .port_scanner import PortScanner
from .port_utils import list_serial_ports
from .serial_manager import SerialManager
from .serial_worker import SerialWorker
from .serial_config import SerialConfig

__all__ = ['SerialManager', 'SerialWorker', 'SerialConfig', 'PortScanner', 'list_serial_ports']

