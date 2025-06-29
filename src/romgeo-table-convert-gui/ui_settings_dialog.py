from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QCheckBox, QComboBox, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
import config
import grid_mgmt

import os
import ast
from pathlib import Path

from logutil import log_function, set_log_level, log

@log_function(level='debug')
def save_config_setting(section: str, key: str, value: str, ini_path: str = grid_mgmt.ROMGEO_APPDATA / 'config.ini'):
    import configparser
    ini_file = Path(ini_path)
    parser = configparser.ConfigParser()

    # Load existing config if it exists
    if ini_file.exists():
        parser.read(ini_file)

    # Ensure the section exists
    if not parser.has_section(section):
        parser.add_section(section)

    # Set or update the value
    parser.set(section, key, str(value))

    # Save back to file
    with open(ini_file, "w", encoding="utf-8") as f:
        parser.write(f)

@log_function(level='debug')
def load_config_overrides(ini_path: None):
    import configparser
    ini_file = Path(ini_path)
    if not ini_file.exists():
        log(f"No config.ini found.", also_print=True)
        return

    parser = configparser.ConfigParser()
    parser.read(ini_file)

    if parser.has_section('SETTINGS'):
        for key, value in parser.items("SETTINGS"):
            key_upper = key.upper()
            if hasattr(config, key_upper):
                current = getattr(config, key_upper)
                # Support comma-separated lists like ZBOX_RO_ETRS
                if isinstance(current, list):
                    try:
                        value = [float(x.strip()) for x in value.split(",")]
                    except:
                        continue
                elif isinstance(current, str):
                    value = str(value)
                elif isinstance(current, bool):    
                    value = True if value == 'True' else False
                elif isinstance(current, int):
                    value = int(value)
                elif isinstance(current, float):
                    value = float(value)

                setattr(config, key_upper, value)
                log(f"Config: OVERWRIDE {key_upper} = {value}", also_print=True)

@log_function(level='debug')
def load_config_settings(ini_path: None, group:str = 'UI'):
    import configparser
    ini_file = Path(ini_path)
    if not ini_file.exists():
        log("No config.ini found.", also_print=True)
        return

    parser = configparser.ConfigParser()
    parser.read(ini_file)

    if group not in parser.sections():
        log(f"Section {group} not found.", also_print=True)
        return 

    for key, value in parser.items(group):
        key_upper = key.upper()

        # Support comma-separated lists like ZBOX_RO_ETRS
        if isinstance(value, list):
            try:
                value = [float(x.strip()) for x in value.split(",")]
            except:
                continue
        elif isinstance(value, str):
            value = str(value)
        elif isinstance(value, bool):    
            value = True if value == 'True' else False
        elif isinstance(value, int):
            value = int(value)
        elif isinstance(value, float):
            value = float(value)

        setattr(config, key_upper, value)
        log(f"Config: Load {key_upper} = {value}", also_print=True, level='debug')


# CONFIG_OVERRIDES = load_config_overrides( grid_mgmt.ROMGEO_APPDATA / "config.ini", "SETTINGS")
# UI_OVERRIDES = load_config_overrides(grid_mgmt.ROMGEO_APPDATA / "config.ini", "UI")



SETTINGS = {
    "EXE_VERSION":            {"type": "str",  "default": config.EXE_VERSION, "label": "Executable version", "DEV_ONLY": True},
    "AUTO_UPDATE":            {"type": "bool", "default": config.AUTO_UPDATE, "label": "Enable auto-update", "DEV_ONLY": False},
    "CHECK_PRERELEASE":       {"type": "bool", "default": config.CHECK_PRERELEASE, "label": "Allow pre-releases", "DEV_ONLY": False},
    "EXE_AUTO_UPDATE":        {"type": "bool", "default": config.EXE_AUTO_UPDATE, "label": "Update binary automatically", "DEV_ONLY": False},
    "DEV":                    {"type": "bool", "default": config.DEV, "label": "Enable developer mode", "DEV_ONLY": False},
    "URL_FAQ":                {"type": "str",  "default": config.URL_FAQ, "label": "FAQ URL", "DEV_ONLY": True},
    "URL_FEEDBACK":           {"type": "str",  "default": config.URL_FEEDBACK, "label": "Feedback URL", "DEV_ONLY": True},
    "LOGLEVEL":               {"type": "enum", "default": config.LOGLEVEL, "label": "Logging level", "options": ["debug", "info", "warning", "error"], "DEV_ONLY": False},
    "DEBUG_MAX_LIST":         {"type": "int",  "default": config.DEBUG_MAX_LIST, "label": "Max debug lines", "DEV_ONLY": False},
    "SWAP_XY_DXF":            {"type": "bool", "default": config.SWAP_XY_DXF, "label": "Swap XY in DXF", "DEV_ONLY": False},
    "SWAP_XY_SHP":            {"type": "bool", "default": config.SWAP_XY_SHP, "label": "Swap XY in SHP", "DEV_ONLY": False},
    "SWAP_LATLON_SHP":        {"type": "bool", "default": config.SWAP_LATLON_SHP, "label": "Swap LatLon in SHP", "DEV_ONLY": False},
    "FMT_SPACE_SIZE":         {"type": "int",  "default": config.FMT_SPACE_SIZE, "label": "Fixed width padding", "DEV_ONLY": False},
    "CHUNK_SIZE":             {"type": "int",  "default": config.CHUNK_SIZE, "label": "Chunk size", "DEV_ONLY": False},
    "MAX_POINTS_FOR_DXF":     {"type": "int",  "default": config.MAX_POINTS_FOR_DXF, "label": "Max DXF points", "DEV_ONLY": False},
    "PREGEX_FLOAT4":          {"type": "str",  "default": config.PREGEX_FLOAT4, "label": "Regex Float4", "DEV_ONLY": True},
    "PREGEX_DMS":             {"type": "str",  "default": config.PREGEX_DMS, "label": "Regex DMS", "DEV_ONLY": True},
    "PREGEX_DMS4":            {"type": "str",  "default": config.PREGEX_DMS4, "label": "Regex DMS4", "DEV_ONLY": True},
    "PREGEX_DMS4_FLIPPED":    {"type": "str",  "default": config.PREGEX_DMS4_FLIPPED, "label": "Regex DMS4 flipped", "DEV_ONLY": True},
    "PREGEX_NAME":            {"type": "str",  "default": config.PREGEX_NAME, "label": "Regex Name", "DEV_ONLY": True},
    "PREGEX_LAT":             {"type": "str",  "default": config.PREGEX_LAT, "label": "Regex Latitude", "DEV_ONLY": True},
    "PREGEX_LON":             {"type": "str",  "default": config.PREGEX_LON, "label": "Regex Longitude", "DEV_ONLY": True},
    "PREGEX_HEIGHT":          {"type": "str",  "default": config.PREGEX_HEIGHT, "label": "Regex Height", "DEV_ONLY": True},
    "BBOX_RO_ST70":           {"type": "list",  "default": ",".join(map(str, config.BBOX_RO_ST70)), "label": "Bounding Box ST70", "DEV_ONLY": True},
    "ZBOX_RO_ST70":           {"type": "list",  "default": ",".join(map(str, config.ZBOX_RO_ST70)), "label": "Z-Box ST70", "DEV_ONLY": True},
    "BBOX_RO_ETRS":           {"type": "list",  "default": ",".join(map(str, config.BBOX_RO_ETRS)), "label": "Bounding Box ETRS89", "DEV_ONLY": True},
    "ZBOX_RO_ETRS":           {"type": "list",  "default": ",".join(map(str, config.ZBOX_RO_ETRS)), "label": "Z-Box ETRS89", "DEV_ONLY": True},
}

SETTINGS_LABELS_RO = {
    "EXE_VERSION": "Versiunea executabilului",
    "AUTO_UPDATE": "Activează actualizarea automată",
    "CHECK_PRERELEASE": "Permite versiuni preliminare",
    "EXE_AUTO_UPDATE": "Actualizează binarul automat",
    "DEV": "Mod dezvoltator",
    "URL_FAQ": "URL pentru întrebări frecvente",
    "URL_FEEDBACK": "URL pentru feedback",
    "LOGLEVEL": "Nivel de jurnalizare",
    "DEBUG_MAX_LIST": "Număr maxim linii debug",
    "SWAP_XY_DXF": "Inversează X/Y în DXF",
    "SWAP_XY_SHP": "Inversează X/Y în SHP",
    "SWAP_LATLON_SHP": "Inversează Lat/Lon în SHP",
    "FMT_SPACE_SIZE": "Spațiere format fix",
    "CHUNK_SIZE": "Dimensiune bloc de procesare",
    "MAX_POINTS_FOR_DXF": "Puncte max pentru DXF",
    "PREGEX_FLOAT4": "Regex pentru coordonate float",
    "PREGEX_DMS": "Regex pentru DMS",
    "PREGEX_DMS4": "Regex pentru DMS cu 4 componente",
    "PREGEX_DMS4_FLIPPED": "Regex DMS4 inversat",
    "PREGEX_NAME": "Regex pentru nume",
    "PREGEX_LAT": "Regex pentru latitudine",
    "PREGEX_LON": "Regex pentru longitudine",
    "PREGEX_HEIGHT": "Regex pentru înălțime",
    "BBOX_RO_ST70": "BBOX ST70 România",
    "ZBOX_RO_ST70": "ZBOX ST70 România",
    "BBOX_RO_ETRS": "BBOX ETRS89 România",
    "ZBOX_RO_ETRS": "ZBOX ETRS89 România"
}

UI_FLAGS = {
    "HIDE_INFO_ETRS_IMPORT":     {"default": getattr(config, "HIDE_INFO_ETRS_IMPORT", False), "label": "Hide ETRS import notice"},
    "HIDE_INFO_ST70_IMPORT":     {"default": getattr(config, "HIDE_INFO_ST70_IMPORT", False), "label": "Hide ST70 import notice"},
    "HIDE_INFO_ETRS_EXPORT_DXF": {"default": getattr(config, "HIDE_INFO_ETRS_EXPORT_DXF", False), "label": "Hide ETRS DXF export notice"},
    "HIDE_INFO_ETRS_EXPORT_XLS": {"default": getattr(config, "HIDE_INFO_ETRS_EXPORT_XLS", False), "label": "Hide ETRS XLS export notice"},
    "HIDE_INFO_ETRS_EXPORT_SHP": {"default": getattr(config, "HIDE_INFO_ETRS_EXPORT_SHP", False), "label": "Hide ETRS SHP export notice"},
    "HIDE_INFO_ST70_EXPORT_DXF": {"default": getattr(config, "HIDE_INFO_ST70_EXPORT_DXF", False), "label": "Hide ST70 DXF export notice"},
    "HIDE_INFO_ST70_EXPORT_XLS": {"default": getattr(config, "HIDE_INFO_ST70_EXPORT_XLS", False), "label": "Hide ST70 XLS export notice"},
    "HIDE_INFO_ST70_EXPORT_SHP": {"default": getattr(config, "HIDE_INFO_ST70_EXPORT_SHP", False), "label": "Hide ST70 SHP export notice"},
}

UI_FLAGS_LABELS_RO = {
    "HIDE_INFO_ETRS_IMPORT":     "Ascunde notificarea de import ETRS",
    "HIDE_INFO_ST70_IMPORT":     "Ascunde notificarea de import ST70",
    "HIDE_INFO_ETRS_EXPORT_DXF": "Ascunde notificarea de export ETRS în DXF",
    "HIDE_INFO_ETRS_EXPORT_XLS": "Ascunde notificarea de export ETRS în XLS",
    "HIDE_INFO_ETRS_EXPORT_SHP": "Ascunde notificarea de export ETRS în SHP",
    "HIDE_INFO_ST70_EXPORT_DXF": "Ascunde notificarea de export ST70 în DXF",
    "HIDE_INFO_ST70_EXPORT_XLS": "Ascunde notificarea de export ST70 în XLS",
    "HIDE_INFO_ST70_EXPORT_SHP": "Ascunde notificarea de export ST70 în SHP",
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RomGEO - Configurare aplicație")
        self.resize(800, 600)
        self.layout = QVBoxLayout(self)

        # re-label for Romanian
        for k, label in SETTINGS_LABELS_RO.items():
            if k in SETTINGS:
                SETTINGS[k]["label"] = label
        for k, label in UI_FLAGS_LABELS_RO.items():
            if k in UI_FLAGS:
                UI_FLAGS[k]["label"] = label

        # Filter SETTINGS based on DEV_ONLY
        visible_settings = {
            k: v for k, v in SETTINGS.items()
            if not v.get("DEV_ONLY") or config.DEV
        }

        self.layout.addWidget(QLabel("Setări aplicație (SETTINGS)"))
        self.settings_table = QTableWidget(len(visible_settings), 3)
        self.settings_table.setHorizontalHeaderLabels(["Nume", "Valoare", "Tip"])
        self.settings_table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.settings_table)

        self.layout.addWidget(QLabel("Preferințe interfață (UI)"))
        self.ui_table = QTableWidget(len(UI_FLAGS), 2)
        self.ui_table.setHorizontalHeaderLabels(["Nume", "Activat"])
        self.ui_table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.ui_table)

        self.save_btn = QPushButton("Salvează modificările")
        self.save_btn.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_btn)

        self.editors = {}

        # load settings before
        try:
            print('Loading config.ini')
            load_config_overrides(grid_mgmt.ROMGEO_APPDATA / 'config.ini')
            load_config_settings (grid_mgmt.ROMGEO_APPDATA / 'config.ini')
        except:
            pass        

        for row, (key, meta) in enumerate(visible_settings.items()):
            label = meta.get("label", key)
            self.settings_table.setItem(row, 0, QTableWidgetItem(label))
            self.settings_table.setItem(row, 2, QTableWidgetItem(meta["type"]))
            value = getattr(config, key)

            if   meta["type"] == "bool":
                widget = QCheckBox()
                widget.setChecked(bool(value))
            elif meta["type"] == "enum":
                widget = QComboBox()
                widget.addItems(meta["options"])
                if value in meta["options"]:
                    widget.setCurrentText(value)
            elif meta["type"] == "list":
                widget = QLineEdit(",".join(map(str, value)))
            else:
                widget = QLineEdit(str(value))

            self.settings_table.setCellWidget(row, 1, widget)
            self.editors[("SETTINGS", key)] = widget

        for row, (key, meta) in enumerate(UI_FLAGS.items()):
            label = meta.get("label", key)
            val = meta.get("default", False)
            self.ui_table.setItem(row, 0, QTableWidgetItem(label))
            widget = QCheckBox()
            widget.setChecked(bool(val))
            self.ui_table.setCellWidget(row, 1, widget)
            self.editors[("UI", key)] = widget

        self.settings_table.resizeColumnsToContents()
        self.ui_table.resizeColumnsToContents()
    
    
    def save_changes(self):

        # # load settings before
        # try:
        #     print('Loading config.ini')
        #     load_config_overrides(grid_mgmt.ROMGEO_APPDATA / 'config.ini')
        #     load_config_settings (grid_mgmt.ROMGEO_APPDATA / 'config.ini')
        # except:
        #     pass

        for (section, key), editor in self.editors.items():

            default = getattr(config, key, None) #if section == "UI" else SETTINGS[key]["default"]

            if isinstance(editor, QCheckBox):
                val = editor.isChecked()
            elif isinstance(editor, QComboBox):
                val = editor.currentText()
            else:
                val = editor.text()
                if SETTINGS.get(key, {}).get("type") == "int":
                    try:
                        val = int(val)
                    except:
                        continue
                elif SETTINGS.get(key, {}).get("type") == "list":
                    default = ",".join(map(str, default))
                    pass
            
            # log(f"Config Compare {key=} {val=} {default=}", also_print=True)

            if str(val) != str(default):
                log(f"Config: SET {key} = {val}", also_print=True)
                save_config_setting(section, key, val, grid_mgmt.ROMGEO_APPDATA / "config.ini")

        self.accept()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar

    class DummyMain(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("RomGEO Settings Tester")
            self.setGeometry(100, 100, 600, 400)
            self.statusbar = QStatusBar()
            self.setStatusBar(self.statusbar)
            self.show()
            dlg = SettingsDialog(self)
            if dlg.exec_():
                self.statusbar.showMessage("Setările au fost salvate.", 3000)

    app = QApplication(sys.argv)
    window = DummyMain()
    
    sys.exit(app.exec_())