# -*- coding: utf-8 -*-
# Copyright (C) 2025  Qilang² <ximing766@gmail.com>
# Crisp SVG icon rendering helpers (pure PySide6 / QtSvg).

from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from PySide6.QtSvg import QSvgRenderer

ICON_DIR = Path(__file__).parent.parent / "assets" / "images" / "svg_icons"

# Cache keyed by (path, size, color, dpr) so repeated paints don't re-rasterize.
_CACHE: dict = {}


def icon_path(name: str) -> str:
    """Resolve an SVG icon name to its absolute path ('' if missing)."""
    p = ICON_DIR / name
    return str(p) if p.exists() else ""


def render_svg(path: str, size: int, color: str = "#ffffff", dpr: float = 1.0) -> QPixmap:
    """Rasterize an SVG at `size` logical px, tinted `color`, sharp on HiDPI.

    Renders directly at the device resolution instead of scaling a small
    rasterization up, which is what made the icons look blurry.
    """
    if not path:
        return QPixmap()

    key = (path, size, color, round(dpr, 2))
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    renderer = QSvgRenderer(path)
    if not renderer.isValid():
        return QPixmap()

    # Respect the SVG's native aspect ratio — fit into a `size x size` logical box.
    default = renderer.defaultSize()  # intrinsic size in SVG units
    if default.isEmpty():
        w_px = h_px = max(1, int(round(size * dpr)))
    else:
        ar = default.width() / max(default.height(), 1)
        if ar >= 1.0:
            w_px = max(1, int(round(size * dpr)))
            h_px = max(1, int(round(size * dpr / ar)))
        else:
            h_px = max(1, int(round(size * dpr)))
            w_px = max(1, int(round(size * dpr * ar)))

    pixmap = QPixmap(w_px, h_px)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, w_px, h_px))
    # Tint: keep alpha, replace RGB
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    pixmap.setDevicePixelRatio(dpr)
    _CACHE[key] = pixmap
    return pixmap


def svg_icon(name: str, size: int = 20, color: str = "#ffffff", dpr: float = 1.0) -> QIcon:
    """Build a QIcon from an SVG icon name, tinted and crisp."""
    pm = render_svg(icon_path(name), size, color, dpr)
    return QIcon(pm) if not pm.isNull() else QIcon()
