# -*- coding: utf-8 -*-
"""MES connection settings.

Values live under the top-level ``"mes"`` section of ``config/config.json``::

    "mes": {
        "enabled": false,
        "base_url": "https://mes.example.com",
        "upload_path": "/api/v1/test-results",
        "api_key": "",
        "timeout": 10,
        "max_retries": 3,
        "verify_tls": true
    }
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import urljoin


@dataclass
class MESConfig:
    """Connection parameters for the MES upload endpoint."""

    enabled: bool = False
    base_url: str = ""
    upload_path: str = "/api/v1/test-results"
    api_key: str = ""
    timeout: float = 10.0
    max_retries: int = 3
    verify_tls: bool = True
    extra_headers: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Derived values
    # ------------------------------------------------------------------

    def upload_url(self) -> str:
        """Absolute upload URL, empty when ``base_url`` is not configured."""
        if not self.base_url:
            return ""
        if self.upload_path.startswith("http://") or self.upload_path.startswith("https://"):
            return self.upload_path
        return urljoin(self.base_url.rstrip("/") + "/", self.upload_path.lstrip("/"))

    def is_configured(self) -> bool:
        """True when uploads have everything they need to be attempted."""
        return bool(self.enabled and self.upload_url())

    def headers(self) -> Dict[str, str]:
        """Request headers including authentication."""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        headers.update(self.extra_headers)
        return headers

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "upload_path": self.upload_path,
            "api_key": self.api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "verify_tls": self.verify_tls,
            "extra_headers": dict(self.extra_headers),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MESConfig":
        return cls(
            enabled=bool(data.get("enabled", False)),
            base_url=str(data.get("base_url", "") or ""),
            upload_path=str(data.get("upload_path", "/api/v1/test-results") or ""),
            api_key=str(data.get("api_key", "") or ""),
            timeout=float(data.get("timeout", 10.0) or 10.0),
            max_retries=max(0, int(data.get("max_retries", 3) or 0)),
            verify_tls=bool(data.get("verify_tls", True)),
            extra_headers=dict(data.get("extra_headers", {}) or {}),
        )

    @classmethod
    def from_config_manager(cls, config_manager) -> "MESConfig":
        """Load from a ``ConfigManager`` instance (returns defaults if absent)."""
        if config_manager is None:
            return cls()
        getter = getattr(config_manager, "get_section", None)
        data = getter("mes") if callable(getter) else {}
        return cls.from_dict(data or {})

    def save(self, config_manager) -> bool:
        """Persist to ``config.json`` through ``ConfigManager``."""
        setter: Optional[Any] = getattr(config_manager, "set_section", None)
        if not callable(setter):
            return False
        setter("mes", self.to_dict())
        return True
