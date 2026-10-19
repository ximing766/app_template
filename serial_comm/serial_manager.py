# -*- coding: utf-8 -*-
"""Serial port manager for handling multiple serial connections."""

import serial
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal

from .port_utils import list_serial_ports
from .serial_config import DATA_BITS, PARITY, STOP_BITS, SerialConfig
from .serial_worker import SerialWorker


class SerialManager(QObject):
    """Manager for multiple serial port connections.

    This is a process-wide singleton: connections stay open across page
    navigation (and page re-creation) until they are closed explicitly by the
    user or lost because the device disappeared / raised an error.
    """

    # Signals
    port_opened = Signal(str, SerialConfig)  # port_id, config
    port_closed = Signal(str)  # port_id
    data_received = Signal(str, bytes)  # port_id, data
    connection_lost = Signal(str, str)  # port_id, error_msg
    error_occurred = Signal(str, str)  # port_id, error_msg

    _instance = None

    @classmethod
    def instance(cls) -> "SerialManager":
        """Return the shared SerialManager instance."""
        if cls._instance is None:
            cls._instance = SerialManager()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connections: Dict[str, dict] = {}  # port_id -> {port, worker, config}
        self._port_counter = 0
    
    def get_available_ports(self) -> List[Tuple[str, str]]:
        """Get list of available serial ports (includes virtual ports).
        
        Returns:
            List of tuples (port_name, description)
        """
        return list_serial_ports()
    
    def generate_port_id(self) -> str:
        """Generate a unique port ID."""
        self._port_counter += 1
        return f"serial_{self._port_counter}"
    
    def open_port(self, config: SerialConfig, port_id: Optional[str] = None) -> Tuple[bool, str, str]:
        """Open a serial port connection.
        
        Args:
            config: Serial port configuration
            port_id: Optional port ID, auto-generated if None
        
        Returns:
            Tuple of (success, port_id, error_message)
        """
        if not config.port:
            return False, "", "No port specified"
        
        if port_id is None:
            port_id = self.generate_port_id()
        
        if port_id in self._connections:
            return False, port_id, f"Port ID {port_id} already in use"

        if self.find_port_id(config.port):
            return False, port_id, f"{config.port} is already open"
        
        try:
            ser = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=DATA_BITS,
                stopbits=STOP_BITS,
                parity=PARITY,
                timeout=config.timeout,
            )
            
            worker = SerialWorker(ser)
            worker.data_received.connect(lambda data: self._on_data_received(port_id, data))
            worker.connection_lost.connect(lambda msg: self._on_connection_lost(port_id, msg))
            worker.error_occurred.connect(lambda msg: self._on_error_occurred(port_id, msg))
            worker.start()
            
            config.is_open = True
            self._connections[port_id] = {
                'port': ser,
                'worker': worker,
                'config': config
            }
            
            self.port_opened.emit(port_id, config)
            return True, port_id, ""
            
        except serial.SerialException as e:
            return False, port_id, f"Failed to open {config.port}: {str(e)}"
        except Exception as e:
            return False, port_id, f"Unexpected error: {str(e)}"
    
    def close_port(self, port_id: str) -> bool:
        """Close a serial port connection.
        
        Args:
            port_id: ID of the port to close
        
        Returns:
            True if closed successfully
        """
        if port_id not in self._connections:
            return False
        
        conn = self._connections[port_id]
        
        try:
            worker = conn['worker']
            if worker.isRunning():
                worker.stop()
            
            port = conn['port']
            if port.is_open:
                port.close()
            
            conn['config'].is_open = False
            del self._connections[port_id]
            
            self.port_closed.emit(port_id)
            return True
            
        except Exception as e:
            self.error_occurred.emit(port_id, f"Error closing port: {str(e)}")
            return False
    
    def close_all_ports(self):
        """Close all open serial port connections."""
        port_ids = list(self._connections.keys())
        for port_id in port_ids:
            self.close_port(port_id)
    
    def write_data(self, port_id: str, data: bytes) -> Tuple[bool, str]:
        """Write data to a serial port.
        
        Args:
            port_id: ID of the port
            data: Data to write
        
        Returns:
            Tuple of (success, error_message)
        """
        if port_id not in self._connections:
            return False, f"Port {port_id} not found"
        
        conn = self._connections[port_id]
        port = conn['port']
        
        try:
            if not port.is_open:
                return False, "Port is not open"
            
            port.write(data)
            return True, ""
            
        except Exception as e:
            error_msg = f"Write error: {str(e)}"
            self.error_occurred.emit(port_id, error_msg)
            return False, error_msg
    
    def get_connection_info(self, port_id: str) -> Optional[SerialConfig]:
        """Get configuration for a connection.
        
        Args:
            port_id: ID of the port
        
        Returns:
            SerialConfig or None if not found
        """
        if port_id in self._connections:
            return self._connections[port_id]['config']
        return None
    
    def get_all_connections(self) -> Dict[str, SerialConfig]:
        """Get all active connections.
        
        Returns:
            Dictionary of port_id -> SerialConfig
        """
        return {
            port_id: conn['config']
            for port_id, conn in self._connections.items()
        }
    
    def is_port_open(self, port_id: str) -> bool:
        """Check if a port is open.
        
        Args:
            port_id: ID of the port
        
        Returns:
            True if port is open
        """
        return port_id in self._connections

    def find_port_id(self, device_name: str) -> Optional[str]:
        """Find the connection ID that owns a physical device (e.g. ``COM3``)."""
        for port_id, conn in self._connections.items():
            if conn['config'].port == device_name:
                return port_id
        return None

    def open_ports(self) -> Dict[str, SerialConfig]:
        """Return only the currently open connections."""
        return {
            port_id: conn['config']
            for port_id, conn in self._connections.items()
            if conn['port'].is_open
        }
    
    def _on_data_received(self, port_id: str, data: bytes):
        """Internal handler for received data."""
        self.data_received.emit(port_id, data)
    
    def _on_connection_lost(self, port_id: str, error_msg: str):
        """Internal handler for connection loss."""
        if port_id in self._connections:
            self._connections[port_id]['config'].is_open = False
        self.connection_lost.emit(port_id, error_msg)
    
    def _on_error_occurred(self, port_id: str, error_msg: str):
        """Internal handler for errors."""
        self.error_occurred.emit(port_id, error_msg)
