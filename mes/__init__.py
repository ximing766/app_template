# -*- coding: utf-8 -*-
"""Company MES integration (test result upload).

This package is a framework stub: the transport, retry policy, payload shape
and Qt signalling are implemented; only the endpoint/field mapping needs to be
aligned with the real MES API.

Layout::

    mes/
    ├── mes_config.py    # connection settings (config.json -> "mes")
    ├── test_record.py   # test result model + JSON payload
    ├── mes_worker.py    # background HTTP upload task
    └── mes_client.py    # Qt-facing client (signals, retry queue)
"""

from .mes_client import MESClient
from .mes_config import MESConfig
from .test_record import TestItem, TestResult

__all__ = ["MESClient", "MESConfig", "TestItem", "TestResult"]
