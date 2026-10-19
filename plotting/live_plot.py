# -*- coding: utf-8 -*-
"""Theme-aware live plotting widget built on pyqtgraph.

Placeholder scaffold for production-test parameter charts. The API is stable
enough to build pages on:

    plot = LivePlotWidget(title="Voltage", y_label="V")
    plot.add_curve("ch1", name="Channel 1", color="#568af2")
    plot.append("ch1", value=3.31)            # x auto-increments
    plot.append("ch1", value=3.29, x=ts)
    plot.clear()

Colors/backgrounds follow the app theme via :meth:`LivePlotWidget.apply_theme`.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:  # optional dependency
    import pyqtgraph as pg
except Exception:  # pragma: no cover - missing optional dependency
    pg = None

MAX_POINTS = 5000

PLOT_COLORS = {
    False: {  # dark
        "background": "transparent",
        "axis": "#9aa3b0",
        "grid": "rgba(255, 255, 255, 0.08)",
        "text": "#c3ccdf",
    },
    True: {   # light
        "background": "transparent",
        "axis": "#6b7280",
        "grid": "rgba(0, 0, 0, 0.08)",
        "text": "#2c3e50",
    },
}


@dataclass
class PlotCurveSpec:
    """Description of a single plotted series."""

    key: str
    name: str = ""
    color: str = "#568af2"
    width: float = 1.4
    auto_x: bool = True
    x: List[float] = field(default_factory=list)
    y: List[float] = field(default_factory=list)

    def trim(self, max_points: int = MAX_POINTS):
        if len(self.y) > max_points:
            extra = len(self.y) - max_points
            del self.y[:extra]
            if self.x:
                del self.x[:extra]


class LivePlotWidget(QWidget):
    """A small wrapper that keeps pyqtgraph usage consistent across pages."""

    def __init__(self, title: str = "", x_label: str = "Sample",
                 y_label: str = "", parent=None):
        super().__init__(parent)
        self._curves: Dict[str, PlotCurveSpec] = {}
        self._plot_items: Dict[str, object] = {}
        self._sample_index = 0
        self._is_light = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        if pg is None:
            self._plot = None
            hint = QLabel(
                "pyqtgraph is not installed.\n"
                "Install it with: pip install pyqtgraph"
            )
            hint.setAlignment(Qt.AlignCenter)
            layout.addWidget(hint)
            self._placeholder = hint
        else:
            self._placeholder = None
            pg.setConfigOptions(antialias=True)
            self._plot = pg.PlotWidget()
            self._plot.setBackground(QColor(0, 0, 0, 0))
            self._plot.showGrid(x=True, y=True, alpha=0.15)
            self._plot.setLabel("bottom", x_label)
            if y_label:
                self._plot.setLabel("left", y_label)
            if title:
                self._plot.setTitle(title, color=PLOT_COLORS[False]["text"])
            self._plot.getPlotItem().setDownsampling(auto=True, mode="peak")
            self._plot.getPlotItem().setClipToView(True)
            layout.addWidget(self._plot)

        self.apply_theme(False)

    # ------------------------------------------------------------------
    # Curves
    # ------------------------------------------------------------------

    def add_curve(self, key: str, name: str = "", color: str = "#568af2",
                  width: float = 1.4) -> PlotCurveSpec:
        """Register a curve; returns its spec."""
        spec = PlotCurveSpec(key=key, name=name or key, color=color, width=width)
        self._curves[key] = spec

        if self._plot is not None:
            pen = pg.mkPen(color=color, width=width)
            item = self._plot.plot([], [], pen=pen, name=spec.name)
            self._plot_items[key] = item
        return spec

    def remove_curve(self, key: str):
        spec = self._curves.pop(key, None)
        item = self._plot_items.pop(key, None)
        if self._plot is not None and item is not None:
            self._plot.removeItem(item)
        return spec

    def append(self, key: str, value: float, x: Optional[float] = None):
        """Append one sample to a curve (x auto-increments when omitted)."""
        spec = self._curves.get(key)
        if spec is None:
            spec = self.add_curve(key)

        if x is None:
            self._sample_index += 1
            x = float(self._sample_index)

        spec.x.append(float(x))
        spec.y.append(float(value))
        spec.trim()

        item = self._plot_items.get(key)
        if item is not None:
            item.setData(spec.x, spec.y)

    def clear(self):
        """Drop all samples but keep the curve definitions."""
        for key, spec in self._curves.items():
            spec.x.clear()
            spec.y.clear()
            item = self._plot_items.get(key)
            if item is not None:
                item.setData([], [])
        self._sample_index = 0

    def clear_curves(self):
        """Remove every curve from the widget."""
        for key in list(self._curves.keys()):
            self.remove_curve(key)
        self._sample_index = 0

    # ------------------------------------------------------------------
    # Appearance
    # ------------------------------------------------------------------

    def apply_theme(self, is_light: bool):
        """Match the application theme."""
        self._is_light = is_light
        colors = PLOT_COLORS[is_light]
        if self._plot is None:
            if self._placeholder is not None:
                self._placeholder.setStyleSheet(
                    f"color: {colors['text']}; background: transparent;"
                )
            return

        axis_color = colors["axis"]
        for name in ("left", "bottom"):
            axis = self._plot.getPlotItem().getAxis(name)
            axis.setPen(pg.mkPen(axis_color))
            axis.setTextPen(pg.mkPen(axis_color))
        self._plot.getPlotItem().getViewBox().setBackgroundColor(None)

    def set_y_range(self, lower: Optional[float], upper: Optional[float]):
        """Fix the Y range, or re-enable auto ranging when a bound is missing."""
        if self._plot is None:
            return
        item = self._plot.getPlotItem()
        if lower is None or upper is None:
            item.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
        else:
            item.setYRange(lower, upper, padding=0)

    def set_x_range(self, lower: Optional[float], upper: Optional[float]):
        """Fix the X range, or re-enable auto ranging when a bound is missing."""
        if self._plot is None:
            return
        item = self._plot.getPlotItem()
        if lower is None or upper is None:
            item.getViewBox().enableAutoRange(axis=pg.ViewBox.XAxis, enable=True)
        else:
            item.setXRange(lower, upper, padding=0)

    def reset_view(self):
        if self._plot is not None:
            self._plot.getPlotItem().enableAutoRange()
