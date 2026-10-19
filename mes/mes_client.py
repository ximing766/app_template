# -*- coding: utf-8 -*-
"""Qt-facing MES client.

Usage::

    from mes import MESClient, MESConfig, TestResult, TestItem

    client = MESClient(MESConfig.from_config_manager(config_manager))
    client.upload_succeeded.connect(lambda rid, body: print("uploaded", rid))
    client.upload_failed.connect(lambda rid, err: print("failed", err))
    client.upload_result(TestResult(serial_number="SN0001"))

Uploads never block the GUI thread (``QThreadPool``) and failed payloads are
kept in a bounded retry queue.
"""

import uuid
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QThreadPool, Signal

from .mes_config import MESConfig
from .mes_worker import MESUploadSignals, MESUploadTask
from .test_record import TestResult

MAX_PENDING_UPLOADS = 50


class MESClient(QObject):
    """Uploads production test results to the company MES."""

    upload_started = Signal(str)              # request_id
    upload_succeeded = Signal(str, dict)      # request_id, response body
    upload_failed = Signal(str, str)          # request_id, error message
    upload_skipped = Signal(str, str)         # request_id, reason
    queue_changed = Signal(int)               # pending payload count

    def __init__(self, config: Optional[MESConfig] = None, parent=None):
        super().__init__(parent)
        self.config = config or MESConfig()
        self._pool = QThreadPool.globalInstance()
        self._pending: List[Dict] = []          # [{request_id, payload}]
        self._tasks: Dict[str, MESUploadTask] = {}   # in-flight, keeps refs
        self._payloads: Dict[str, Dict] = {}    # request_id -> payload

        # Owned here so queued cross-thread signals always have a live receiver.
        self._upload_signals = MESUploadSignals(self)
        self._upload_signals.succeeded.connect(self._on_succeeded)
        self._upload_signals.failed.connect(self._on_failed)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure(self, config: MESConfig):
        self.config = config

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_result(self, result: TestResult) -> str:
        """Queue a :class:`TestResult` for upload; returns the request id."""
        return self.upload_payload(result.to_payload())

    def upload_payload(self, payload: Dict, request_id: Optional[str] = None) -> str:
        """Queue a raw JSON payload for upload; returns the request id."""
        request_id = request_id or uuid.uuid4().hex

        if not self.config.enabled:
            self.upload_skipped.emit(request_id, "MES upload disabled")
            return request_id
        if not self.config.is_configured():
            self.upload_skipped.emit(request_id, "MES endpoint not configured")
            return request_id

        self._dispatch(request_id, payload)
        return request_id

    def retry_pending(self):
        """Re-dispatch every payload that previously failed."""
        pending, self._pending = self._pending, []
        self.queue_changed.emit(len(self._pending))
        for entry in pending:
            self._dispatch(entry["request_id"], entry["payload"])

    def clear_pending(self):
        self._pending.clear()
        self.queue_changed.emit(0)

    def pending_count(self) -> int:
        return len(self._pending)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _dispatch(self, request_id: str, payload: Dict):
        task = MESUploadTask(
            request_id=request_id,
            url=self.config.upload_url(),
            payload=payload,
            headers=self.config.headers(),
            signals=self._upload_signals,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            verify_tls=self.config.verify_tls,
        )

        # Keep the task and payload alive until the completion signal arrives.
        self._tasks[request_id] = task
        self._payloads[request_id] = payload

        self.upload_started.emit(request_id)
        self._pool.start(task)

    def _on_succeeded(self, request_id: str, body: Dict):
        self._tasks.pop(request_id, None)
        self._payloads.pop(request_id, None)
        self.upload_succeeded.emit(request_id, body)

    def _on_failed(self, request_id: str, message: str):
        self._tasks.pop(request_id, None)
        payload = self._payloads.pop(request_id, None)
        if payload is not None:
            self._enqueue_for_retry(request_id, payload)
        self.upload_failed.emit(request_id, message)

    def _enqueue_for_retry(self, request_id: str, payload: Dict):
        self._pending.append({"request_id": request_id, "payload": payload})
        if len(self._pending) > MAX_PENDING_UPLOADS:
            self._pending.pop(0)
        self.queue_changed.emit(len(self._pending))
