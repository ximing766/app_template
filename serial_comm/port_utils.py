# -*- coding: utf-8 -*-
"""Serial port enumeration helpers.

``serial.tools.list_ports.comports()`` misses some virtual ports on Windows
(for example com0com pairs) because they are not enumerated through SetupAPI.
The driver map under ``HARDWARE\\DEVICEMAP\\SERIALCOMM`` lists every COM port
the kernel knows about, so both sources are merged here.
"""

import sys
from typing import List, Tuple

import serial.tools.list_ports


def _registry_ports() -> List[Tuple[str, str]]:
    """Read COM ports from the Windows device map (includes virtual ports)."""
    if sys.platform != "win32":
        return []

    import winreg

    entries: List[Tuple[str, str]] = []
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
    except OSError:
        return entries

    try:
        index = 0
        while True:
            try:
                name, device, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            index += 1
            if not isinstance(device, str):
                continue
            friendly = name.rsplit("\\", 1)[-1]
            if "com0com" in friendly.lower():
                description = f"com0com virtual port ({friendly})"
            else:
                description = friendly
            entries.append((device, description))
    finally:
        winreg.CloseKey(key)

    return entries


def list_serial_ports() -> List[Tuple[str, str]]:
    """Return ``(device, description)`` for every available serial port."""
    found = {}

    try:
        for port in serial.tools.list_ports.comports():
            if port.device:
                found[port.device] = port.description or "Serial device"
    except Exception:
        # A broken driver must not hide the registry results.
        pass

    for device, description in _registry_ports():
        found.setdefault(device, description)

    return list(found.items())
