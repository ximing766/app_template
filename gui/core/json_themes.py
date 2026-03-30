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

# IMPORT PACKAGES AND MODULES
# ///////////////////////////////////////////////////////////////
import json
import os

# IMPORT SETTINGS
# ///////////////////////////////////////////////////////////////
from gui.core.json_settings import Settings

# APP THEMES
# ///////////////////////////////////////////////////////////////
class Themes(object):
    _instance = None
    _items = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Themes, cls).__new__(cls)
            cls._instance._init_themes()
        return cls._instance

    def _init_themes(self):
        # Load settings to get the current theme name
        setup_settings = Settings()
        _settings = setup_settings.items

        # APP PATH
        theme_name = _settings.get('theme_name', 'default')
        json_file = f"config/themes/{theme_name}.json"
        app_path = os.path.abspath(os.getcwd())
        self.settings_path = os.path.normpath(os.path.join(app_path, json_file))

        # DICTIONARY WITH SETTINGS
        self.items = {}

        # DESERIALIZE
        self.deserialize()

    # REFRESH THEME
    # ///////////////////////////////////////////////////////////////
    def refresh(self):
        self._init_themes()

    # SERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def serialize(self):
        # WRITE JSON FILE
        with open(self.settings_path, "w", encoding='utf-8') as write:
            json.dump(self.items, write, indent=4)

    # DESERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def deserialize(self):
        # READ JSON FILE
        with open(self.settings_path, "r", encoding='utf-8') as reader:
            settings = json.loads(reader.read())
            self.items = settings
