# -*- coding: utf-8 -*-
"""Parameter plotting (pyqtgraph) — framework stub.

``LivePlotWidget`` is a theme-aware container around a pyqtgraph ``PlotWidget``
with a bounded ring buffer per curve, so later production-test pages can stream
measurements without writing plotting plumbing again.

pyqtgraph is imported lazily: the rest of the app keeps working (with a clear
placeholder message) when the optional dependency is missing.
"""

from .live_plot import LivePlotWidget, PlotCurveSpec

__all__ = ["LivePlotWidget", "PlotCurveSpec"]
