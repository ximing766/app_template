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

# APP SETTINGS
# ///////////////////////////////////////////////////////////////
class Settings(object):
    _instance = None
    _items = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self):
        # APP PATH
        # ///////////////////////////////////////////////////////////////
        self.json_file = "config/config.json"
        self.app_path = os.path.abspath(os.getcwd())
        self.settings_path = os.path.normpath(os.path.join(self.app_path, self.json_file))
        if not os.path.isfile(self.settings_path):
            print(f"WARNING: \"config/config.json\" not found! check in the folder {self.settings_path}")

        # DICTIONARY WITH SETTINGS
        # Just to have objects references
        self.items = {}

        # DESERIALIZE
        self.deserialize()

    # REFRESH SETTINGS
    # ///////////////////////////////////////////////////////////////
    def refresh(self):
        self.deserialize()

    # SERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def serialize(self):
        # READ FULL CONFIG FIRST
        with open(self.settings_path, "r", encoding='utf-8') as reader:
            full_config = json.loads(reader.read())

        # UPDATE ONEDARK SECTION
        full_config['onedark'] = self.items
        
        # Sync back to main theme setting
        theme_name = self.items.get('theme_name', 'default')
        if theme_name == 'bright_theme':
            if 'theme' not in full_config: full_config['theme'] = {}
            full_config['theme']['current_theme'] = 'light'
        else:
            if 'theme' not in full_config: full_config['theme'] = {}
            full_config['theme']['current_theme'] = 'dark'

        # WRITE JSON FILE
        with open(self.settings_path, "w", encoding='utf-8') as write:
            json.dump(full_config, write, indent=4)

    # DESERIALIZE JSON
    # ///////////////////////////////////////////////////////////////
    def deserialize(self):
        # READ JSON FILE
        with open(self.settings_path, "r", encoding='utf-8') as reader:
            full_config = json.loads(reader.read())
            self.items = full_config.get('onedark', {})
            
            # Sync with main theme setting
            main_theme = full_config.get('theme', {}).get('current_theme', 'dark')
            if main_theme == 'light':
                self.items['theme_name'] = 'bright_theme'
            else:
                self.items['theme_name'] = 'default'
