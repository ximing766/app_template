# ///////////////////////////////////////////////////////////////
#
# BY: WANDERSON M.PIMENTA
# PROJECT MADE WITH: Qt Designer and PySide6
# V: 1.0.0
#
# This project can be used freely for all uses, as long as they maintain the
# respective credits only in the Python scripts, any information in the visual
# interface (GUI) can be modified without any implication.
#
# There are limitations on Qt licenses if you want to use your products
# commercially, I recommend reading them on the official website:
# https://doc.qt.io/qtforpython/licenses.html
#
# ///////////////////////////////////////////////////////////////

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

style = """
/* QSlider - Minimalist Template */
QSlider {{ background: transparent; }}
QSlider::groove:horizontal {{ background: {_bg_color}; height: {_bg_size}px; border-radius: {_bg_radius}px; }}
QSlider::handle:horizontal {{ background: {_handle_color}; width: 4px; height: 12px; margin: -4px 0; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {_handle_color}; border-radius: {_bg_radius}px; }}

QSlider::groove:vertical {{ background: {_bg_color}; width: {_bg_size}px; border-radius: {_bg_radius}px; }}
QSlider::handle:vertical {{ background: {_handle_color}; width: 12px; height: 4px; margin: 0 -4px; border-radius: 2px; }}
QSlider::sub-page:vertical {{ background: {_handle_color}; border-radius: {_bg_radius}px; }}
"""

class PySlider(QSlider):
    def __init__(
        self,
        bg_size = 4,
        bg_radius = 2,
        bg_color = "#2c313a",
        handle_color = "#568af2",
        parent = None
    ):
        super().__init__(parent)

        # APPLY CUSTOM STYLE
        self.setStyleSheet(style.format(
            _bg_size = bg_size,
            _bg_radius = bg_radius,
            _bg_color = bg_color,
            _handle_color = handle_color
        ))