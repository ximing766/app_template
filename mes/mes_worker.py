# -*- coding: utf-8 -*-
"""Background HTTP upload task for the MES client.

``urllib`` is used so the app does not depend on ``requests``. The task runs on
a ``QThreadPool`` thread and reports through a :class:`MESUploadSignals`
instance owned by the client — the runnable itself does not own a QObject, so
queued signal delivery cannot be lost when the task is released.
"""

import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, QRunnable, Signal

# Backoff between retries: 0.5s, 1s, 2s, ... capped at 4s.
RETRY_BASE_DELAY = 0.5
RETRY_MAX_DELAY = 4.0


class MESUploadSignals(QObject):
    """Emitter owned by the client (kept alive for the client's lifetime)."""

    succeeded = Signal(str, dict)   # request_id, response body
    failed = Signal(str, str)       # request_id, error message


class MESUploadTask(QRunnable):
    """POST one JSON payload to the MES endpoint with bounded retries."""

    def __init__(
        self,
        request_id: str,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        signals: MESUploadSignals,
        timeout: float = 10.0,
        max_retries: int = 3,
        verify_tls: bool = True,
    ):
        super().__init__()
        # The client owns the task reference and releases it on completion.
        self.setAutoDelete(False)
        self.request_id = request_id
        self.url = url
        self.payload = payload
        self.headers = headers
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.verify_tls = verify_tls
        self.signals = signals

    # ------------------------------------------------------------------

    def run(self):
        body = json.dumps(self.payload, ensure_ascii=False).encode("utf-8")
        context: Optional[ssl.SSLContext] = None
        if not self.verify_tls:
            context = ssl._create_unverified_context()

        last_error = "unknown error"
        attempts = self.max_retries + 1

        for attempt in range(attempts):
            try:
                request = urllib.request.Request(
                    self.url, data=body, headers=self.headers, method="POST"
                )
                with urllib.request.urlopen(request, timeout=self.timeout, context=context) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    parsed = self._parse(raw)
                    self.signals.succeeded.emit(self.request_id, parsed)
                    return
            except urllib.error.HTTPError as exc:
                detail = self._read_error_body(exc)
                last_error = f"HTTP {exc.code}: {detail}"
                # 4xx (except 408/429) will not succeed on retry.
                if 400 <= exc.code < 500 and exc.code not in (408, 429):
                    break
            except urllib.error.URLError as exc:
                last_error = f"Connection failed: {exc.reason}"
            except Exception as exc:  # timeouts, TLS, DNS, malformed response
                last_error = f"{type(exc).__name__}: {exc}"

            if attempt < attempts - 1:
                time.sleep(min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY))

        self.signals.failed.emit(self.request_id, last_error)

    # ------------------------------------------------------------------

    @staticmethod
    def _parse(raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
        return parsed if isinstance(parsed, dict) else {"data": parsed}

    @staticmethod
    def _read_error_body(exc: urllib.error.HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            return exc.reason or str(exc.code)
