# -*- coding: utf-8 -*-
"""Serial port configuration and constants."""

from dataclasses import dataclass


COMMON_BAUDRATES = [9600, 115200, 230400, 460800, 921600, 
                    1000000, 2000000, 3000000]
DATA_BITS = 8
STOP_BITS = 1
PARITY = "N"


@dataclass
class SerialConfig:
    """Configuration for a serial port connection."""

    port: str = ""
    baudrate: int = 115200
    timeout: float = 0.1
    is_open: bool = False

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SerialConfig':
        """Create config from dictionary."""
        return cls(
            port=data.get('port', ''),
            baudrate=data.get('baudrate', 115200),
            timeout=data.get('timeout', 0.1),
        )
