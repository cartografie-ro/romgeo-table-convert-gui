try:
    import pyi_splash # type: ignore
    pyi_splash.update_text("Loading RomGEO Table Convert GUI...")
except ImportError:
    pyi_splash = None

from logutil import log_function, set_log_level, log

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QComboBox
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QDesktopServices
from PyQt5.QtCore import Qt, QUrl

import sys
import numpy as np
from pathlib import Path
from markdown import markdown

from help_overlay import HelpOverlay
from ui_romgeo_table_convert_main import Ui_MainWindow

import config
from functions     import convert_etrs_st70, convert_st70_etrs89, _dd2dms, _is_ascii_file, _fmt
from functions_gis import save_st70_as_shape, save_st70_as_excel, save_st70_as_dxf, save_etrs_as_shape, save_etrs_as_dxf, save_etrs_as_excel
import grid_mgmt 

import ui_info_dialog

class RomgeoLoader(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            import time
            t0 = time.perf_counter()

            global romgeo
            import romgeo_lite as romgeo  # global assignment allows usage across the app           

            t1 = time.perf_counter()
            print(f"[DEBUG] Modulul romgeo a fost importat în {t1 - t0:.3f} secunde. {romgeo.__file__}")            

            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))



class RomgeoTableConvertApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("RomGEO Table Convert GUI")
        self.ui.statusbar.showMessage("Se încarcă grid-ul...")

        self.setup_connections()  # setup button action connections

        # Set up background thread for module loading
        self.ui.pushButton_etrs_st70.setEnabled(False)
        self.ui.pushButton_st70_etrs.setEnabled(False)
        self.loader_thread = QThread()
        self.loader_worker = RomgeoLoader()
        self.loader_worker.moveToThread(self.loader_thread)

        # Connect signals
        self.loader_thread.started.connect(self.loader_worker.run)
        self.loader_worker.finished.connect(self.on_romgeo_loaded)
        self.loader_worker.error.connect(self.on_romgeo_error)

        # Start loading
        self.loader_thread.start()
        

        
    def on_romgeo_loaded(self):
        self.ui.statusbar.showMessage("Grid încărcat cu succes")
        self.ui.pushButton_etrs_st70.setEnabled(True)
        self.ui.pushButton_st70_etrs.setEnabled(True)
        self.loader_thread.quit()
        self.loader_thread.wait()

    def on_romgeo_error(self, msg):
        self.ui.statusbar.showMessage(f"Eroare la încărcare: {msg}")
        self.loader_thread.quit()
        self.loader_thread.wait()

    def _with_buttons_disabled(self, func):
        def wrapped():
            self.ui.frame_main_transform.setEnabled(False)   
            self.ui.statusbar.showMessage("Asteptati...")
            QApplication.processEvents()         
            try:
                func()
            finally:
                self.ui.frame_main_transform.setEnabled(True)
                QApplication.processEvents()
        return wrapped

    def toggle_help_overlay(self):

        if not hasattr(self,'help_overlay'):
            self.help_overlay = HelpOverlay(self)

        self.help_overlay.resize(self.size())
        self.help_overlay.setVisible(not self.help_overlay.isVisible())

    @log_function(level='info')
    def switch_to_multigrid(self, filelist):
        layout = self.ui.frame_top  # This is a QHBoxLayout

        # Get index of the label
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget == self.ui.label_info_center:
                break
        else:
            return  # not found

        # Remove label
        layout.removeWidget(self.ui.label_info_center)
        self.ui.label_info_center.hide()

        # Create and insert combo
        combo = QComboBox(self)
        
        grids = [Path(f).name for f in filelist]

        combo.addItems(grids)
        layout.insertWidget(i, combo)

        self.ui.combo_info_center = combo  # Save reference if needed

        return self.ui.combo_info_center

    def popup_info_modal(self, setting:str, message:str = "message", align = Qt.AlignLeft):

        if not setting:
            # force Dialog
            dialog = ui_info_dialog.InfoDialog(message, self, align)
            dialog.checkbox.setVisible(False)
            dialog.exec_()

        else:
            try:
                load_config_settings(grid_mgmt.ROMGEO_APPDATA / 'config.ini',"UI")
            except:
                pass

            hide_popup = getattr(config, setting.upper(), False)

            if not hide_popup:
                dialog = ui_info_dialog.InfoDialog(message, self, align)
                if dialog.exec_() and dialog.should_hide_future():
                    # Set a flag or update settings to suppress future display
                    save_config_setting("UI", setting.upper(), dialog.should_hide_future(), grid_mgmt.ROMGEO_APPDATA / 'config.ini')
                    print("User chose to hide this message in the future.")


    def setup_connections(self):
        # info
        self.ui.pushButton_info_info.clicked.connect(self.toggle_help_overlay)
        self.ui.pushButton_info_help.clicked.connect(lambda x: QDesktopServices.openUrl(QUrl(config.URL_FAQ)))

        # help
        self.ui.toolButton_etrs_help.clicked.connect(lambda L: self.popup_info_modal(None, config.ETRS_INPUT_HELP))
        self.ui.toolButton_st70_help.clicked.connect(lambda L: self.popup_info_modal(None, config.ST70_INPUT_HELP))
        self.ui.toolButton_etrs_export_help.clicked.connect(lambda L: self.popup_info_modal(None, config.ETRS_EXPORT_HELP))
        self.ui.toolButton_st70_export_help.clicked.connect(lambda L: self.popup_info_modal(None, config.ST70_EXPORT_HELP))


        # text utils
        self.ui.toolButton_etrs_clear.clicked.connect(self._with_buttons_disabled(self.clear_text_etrs))
        self.ui.toolButton_st70_clear.clicked.connect(self._with_buttons_disabled(self.clear_text_st70))
        self.ui.toolButton_etrs_import.clicked.connect(self._with_buttons_disabled(self.import_file_etrs))
        self.ui.toolButton_st70_import.clicked.connect(self._with_buttons_disabled(self.import_file_st70))
        self.ui.toolButton_etrs_save.clicked.connect(self._with_buttons_disabled(self.save_file_etrs))
        self.ui.toolButton_st70_save.clicked.connect(self._with_buttons_disabled(self.save_file_st70))

        # main converts
        self.ui.pushButton_etrs_st70.clicked.connect(self._with_buttons_disabled(self.convert_etrs_to_stereo))
        self.ui.pushButton_st70_etrs.clicked.connect(self._with_buttons_disabled(self.convert_stereo_to_etrs))

        # exports et70
        self.ui.pushButton_st70_export_dxf.clicked.connect(self._with_buttons_disabled(self.st70_export_dxf))
        self.ui.pushButton_st70_export_xls.clicked.connect(self._with_buttons_disabled(self.st70_export_xls))
        self.ui.pushButton_st70_export_shp.clicked.connect(self._with_buttons_disabled(self.st70_export_shp))

        # exports etrs
        self.ui.pushButton_etrs_export_dxf.clicked.connect(self._with_buttons_disabled(self.etrs_export_dxf))
        self.ui.pushButton_etrs_export_xls.clicked.connect(self._with_buttons_disabled(self.etrs_export_xls))
        self.ui.pushButton_etrs_export_shp.clicked.connect(self._with_buttons_disabled(self.etrs_export_shp))

        # Action Menus
        self.ui.actionAjutor_Online.triggered.connect(lambda x: QDesktopServices.openUrl(QUrl(config.URL_FAQ)))
        self.ui.actionFeedback.triggered.connect(lambda x: QDesktopServices.openUrl(QUrl(config.URL_FEEDBACK)))
        self.ui.actionIesire.triggered.connect(QApplication.quit)
        self.ui.actionImport_ETRS.triggered.connect(self._with_buttons_disabled(self.import_file_etrs))
        self.ui.actionImport_Stereo70.triggered.connect(self._with_buttons_disabled(self.import_file_st70))
        self.ui.actionSetari_aplicatie.triggered.connect(self._with_buttons_disabled(self.OpenSettings))

        #


    @log_function(level='debug')
    def st70_export_dxf(self):

        self.popup_info_modal("HIDE_INFO_st70_export_dxf", config.EXPORT_POPUP_HELP_DXF_ST70)

        raw_text = self.ui.textEdit_etrs.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return


        try:
            results = convert_etrs_st70(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier DXF",
            "",
            "Fișier DXF (*.dxf);;Toate fișierele (*)"
        )

        if not file_path:
            self.ui.statusbar.showMessage("Salvarea a fost anulată.")
            return

        save_st70_as_dxf(results, file_path)

        self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")        
        return file_path
    
    @log_function(level='debug')
    def st70_export_xls(self):
        self.popup_info_modal("HIDE_INFO_st70_export_xls",config.EXPORT_POPUP_HELP_XLS_ST70)

        raw_text = self.ui.textEdit_etrs.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return

        try:
            results = convert_etrs_st70(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier XLS",
            "",
            "Fișier XLS (*.xls);;Toate fișierele (*)"
        )

        if not file_path:
            self.ui.statusbar.showMessage("Salvarea a fost anulată.")
            return

        save_st70_as_excel(results, file_path)

        self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")        
        return
    
    @log_function(level='debug')
    def st70_export_shp(self):
        self.popup_info_modal("HIDE_INFO_st70_export_shp", config.EXPORT_POPUP_HELP_SHP_ST70)
        
        raw_text = self.ui.textEdit_etrs.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return

        try:
            results = convert_etrs_st70(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier shp",
            "",
            "Fișier shp (*.shp);;Toate fișierele (*)"
        )

        if not file_path:
            self.ui.statusbar.showMessage("Salvarea a fost anulată.")
            return

        save_st70_as_shape(results, file_path)

        self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")           
        return
    

    @log_function(level='debug')
    def etrs_export_dxf(self):
        self.popup_info_modal("HIDE_INFO_etrs_export_dxf", config.EXPORT_POPUP_HELP_DXF_ETRS)
       
        raw_text = self.ui.textEdit_etrs.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return

        try:
            results = convert_etrs_st70(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier dxf",
            "",
            "Fișier dxf (*.dxf);;Toate fișierele (*)"
        )

        if not file_path:
            self.ui.statusbar.showMessage("Salvarea a fost anulată.")
            return

        save_etrs_as_dxf(results, file_path)

        self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")          
        return
    
    @log_function(level='debug')
    def etrs_export_xls(self):
        self.popup_info_modal("HIDE_INFO_etrs_export_xls", config.EXPORT_POPUP_HELP_XLS_ETRS)
       
        raw_text = self.ui.textEdit_st70.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return

        try:
            results = convert_st70_etrs89(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier XLS",
            "",
            "Fișier XLS (*.xls);;Toate fișierele (*)"
        )

        if not file_path:
            self.ui.statusbar.showMessage("Salvarea a fost anulată.")
            return

        save_etrs_as_excel(results, file_path)

        self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")  
        return
    
    @log_function(level='debug')
    def etrs_export_shp(self):
        self.popup_info_modal("HIDE_INFO_etrs_export_shp", config.EXPORT_POPUP_HELP_SHP_ETRS)
      
        raw_text = self.ui.textEdit_st70.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return

        try:
            results = convert_st70_etrs89(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier SHP",
            "",
            "Fișier SHP (*.shp);;Toate fișierele (*)"
        )

        if not file_path:
            self.ui.statusbar.showMessage("Salvarea a fost anulată.")
            return

        save_etrs_as_shape(results, file_path)

        self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")  
        return



    @log_function(level='info')
    def convert_etrs_to_stereo(self):
        raw_text = self.ui.textEdit_etrs.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return


        try:
            results = convert_etrs_st70(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return
        

        if "SPATIU" in self.ui.comboBox_separator.currentText().upper():
            output_lines = [
                f"{p:<8} {_fmt(x, 11, '.3f')} {_fmt(y, 11, '.3f')} {_fmt(z, 11, '.3f')}"
                for p, n, e, h, x, y, z in results
            ]

        if "TAB" in self.ui.comboBox_separator.currentText().upper():
            output_lines = [
                f"{p}\t{x:.3f}\t{y:.3f}\t{z:.3f}"
                for p, n, e, h, x, y, z in results
            ]

        if "VIRGULA" in self.ui.comboBox_separator.currentText().upper():
            output_lines = [
                f"{p},{x:.3f},{y:.3f},{z:.3f}"
                for p, n, e, h, x, y, z in results
            ]        


        self.ui.textEdit_st70.setPlainText("\n".join(output_lines))
        success_count = sum(1 for _, _, _, _, x, y, z in results if not np.isnan(x) and not np.isnan(y) and not np.isnan(z))
        error_count = len(results) - success_count

        msg = f"{success_count} puncte convertite cu succes."
        if error_count > 0:
            msg += f" {error_count} rânduri cu erori."

        self.ui.statusbar.showMessage(msg)

    @log_function(level='info')
    def convert_stereo_to_etrs(self):
        raw_text = self.ui.textEdit_st70.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            self.ui.statusbar.showMessage("Nu există date de convertit.")
            return

        try:
            results = convert_st70_etrs89(lines)
        except Exception as e:
            self.ui.statusbar.showMessage(f"Eroare la conversie: {e}")
            return

        # Get format setting from comboBox_dms
        use_dms = "DMS" in self.ui.comboBox_dms.currentText().upper()

        output_lines = []
        for p, e, n, h, lat, lon, z in results:
            if use_dms and not np.isnan(lat) and not np.isnan(lon):
                lat_fmt = _dd2dms(lat, format="string")
                lon_fmt = _dd2dms(lon, format="string")
            else:
                lat_fmt = _fmt(lat, 11, '.9f')
                lon_fmt = _fmt(lon, 11, '.9f')

            z_fmt = _fmt(z, 8, '.3f')

            sep = " "
            sep = "\t" if "TAB" in self.ui.comboBox_separator.currentText().upper() else sep
            sep = "," if "VIRGULA" in self.ui.comboBox_separator.currentText().upper() else sep

            output_lines.append(f"{p:<8}{sep}{lat_fmt}{sep}{lon_fmt}{sep}{z_fmt}")


        self.ui.textEdit_etrs.setPlainText("\n".join(output_lines))

        success_count = sum(
            1 for _, _, _, _, lat, lon, z in results
            if not np.isnan(lat) and not np.isnan(lon) and not np.isnan(z)
        )
        error_count = len(results) - success_count

        msg = f"{success_count} puncte convertite cu succes."
        if error_count > 0:
            msg += f" {error_count} rânduri cu erori."

        self.ui.statusbar.showMessage(msg)




    def clear_text_etrs(self):
        self.ui.textEdit_etrs.clear()
        self.ui.statusbar.showMessage("Lista ETRS89 a fost ștearsă.")

    def clear_text_st70(self):
        self.ui.textEdit_st70.clear()
        self.ui.statusbar.showMessage("Lista Stereo70 a fost ștearsă.")


    @log_function(level='info')
    def import_file_etrs(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Deschide fișier ETRS89", "","Fișiere text (*.txt *.csv);;Toate fișierele (*)" )
        if file_path:
            if _is_ascii_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.ui.textEdit_etrs.setPlainText(content)
                    self.ui.statusbar.showMessage(f"Fișier ETRS89 încărcat: {file_path}")
                except Exception as e:
                    self.ui.statusbar.showMessage(f"Eroare la încărcarea fișierului: {e}")
            else:
                self.ui.statusbar.showMessage(f"Fișierul {file_path} nu este in format text.")

    @log_function(level='info')
    def import_file_st70(self):
        file_path, _ = QFileDialog.getOpenFileName(self,"Deschide fișier Stereo70", "","Fișiere text (*.txt *.csv);;Toate fișierele (*)")
        if file_path:
            if _is_ascii_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.ui.textEdit_st70.setPlainText(content)
                    self.ui.statusbar.showMessage(f"Fișier Stereo70 încărcat: {file_path}")
                except Exception as e:
                    self.ui.statusbar.showMessage(f"Eroare la încărcarea fișierului: {e}")
            else:
                self.ui.statusbar.showMessage(f"Fișierul {file_path} nu este in format text.")


    @log_function(level='debug')
    def save_file_etrs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier ETRS89",
            "",
            "Fișier text (*.txt);;Toate fișierele (*)"
        )
        if file_path:
            try:
                content = self.ui.textEdit_etrs.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")
            except Exception as e:
                self.ui.statusbar.showMessage(f"Eroare la salvare: {e}")

    @log_function(level='debug')
    def save_file_st70(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează fișier Stereo70",
            "",
            "Fișier text (*.txt);;Toate fișierele (*)"
        )
        if file_path:
            try:
                content = self.ui.textEdit_st70.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.ui.statusbar.showMessage(f"Fișier salvat: {file_path}")
            except Exception as e:
                self.ui.statusbar.showMessage(f"Eroare la salvare: {e}")


    @log_function(level='debug')
    def OpenSettings(self):
        pass

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
        log(f"No config.ini found.",also_print=True)
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
                log(f"[config override] {key_upper} = {value}", also_print=True)

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
        log(f"[config load] {key_upper} = {value}", also_print=True)

@log_function(level='debug')
def _get_exe_version() -> str:

    import re

    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source
        base_path = Path(__file__).resolve().parent

    version_file = base_path / 'version_info.txt'
    if not version_file.exists():
        return None

    content = version_file.read_text(encoding='utf-8')
    
    r1 = r'filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)'
    r2 = r"StringStruct\(u?'FileVersion', u?'([^']+)'\)"
    match = re.search(r1, content)
    if match:
        return '.'.join(match.groups())
    return None

def enable_developer_mode(window):
    if config.DEV:
        GRID_FILEs = list(Path(grid_mgmt.ROMGEO_GRID_DIR).glob('*.spg'))
        GRID_FILEs.sort()

        if len(GRID_FILEs) > 1:
            combo = window.switch_to_multigrid(GRID_FILEs)

            def handle_grid_change(filename):
                grid_mgmt.set_active_grid_file(filename, grid_mgmt.ROMGEO_GRID_DIR)
                window.ui.statusbar.showMessage(f"Grid-ul {grid_mgmt.ROMGEO_GRID_VER} selectat.")
                
            combo.currentTextChanged.connect(handle_grid_change)

def check_grid_git_prerelease():
    pre_release_text = pre_release = pre_release_date = ''
    if config.CHECK_PRERELEASE:
        try:
            pre_release, pre_release_date = grid_mgmt.git_get_prerelease()

            if grid_mgmt._compact_release_text(pre_release) != grid_mgmt.ROMGEO_GRID_VER:
                from datetime import datetime
                valid_from = datetime.fromisoformat(pre_release_date)
                pre_release_text = f"<br /> <span style=\" font-size:8pt; color:red;\">GRID nou vers. {grid_mgmt._compact_release_text(pre_release)}, va intra in vigoare la {valid_from:%d/%m/%Y}. </span>"
        except:
            pass
    return pre_release_text

def check_grid_git_updates():
    if config.AUTO_UPDATE:
        ## Update and grid set Attempt
        try:
            grid_mgmt.do_online_grid_update()
        except:
            pass

def check_exe_git_updates():
    if config.EXE_AUTO_UPDATE:
        ## Update and grid set Attempt
        try:
            latest_exe = grid_mgmt.git_get_exe_version(f"v{_get_exe_version()}")
            return latest_exe
        
        except:
            return None

def check_exe_update(window):
    new_release_info = check_exe_git_updates()
    if new_release_info:
        window.popup_info_modal("", '<br>'.join(
                [
                    f"A fost lansată o nouă versiune: <strong>{new_release_info['latest_version']}</strong>",
                    f"<em>{new_release_info['release_name']}</em> publicată pe {new_release_info['published_at'].split('T')[0]}<br>",
                    f"Descriere: {markdown(new_release_info['body'])}<br>",
                    "Pachetul este disponibil pentru descărcare la linkul de mai jos:<br>",
                    f"<a href=\"{new_release_info['assets'][0]['download_url']}\">{new_release_info['assets'][0]['name']}</a>",
                    f"(dimensiune: {round(new_release_info['assets'][0]['size'] / (1024**2), 1)} MB)<br>",
                    "Pentru a descărca, apăsați pe link sau faceți click dreapta, alegeți <em>Copy link</em>, apoi inserați-l în browser."
                ]
            )
        )

def select_grid(window):
    try:
        _, _ = grid_mgmt.select_best_grid()
        print(f"Activated {grid_mgmt.ROMGEO_GRID_FILE=}, {grid_mgmt.ROMGEO_GRID_VER=}")
        window.ui.statusbar.showMessage(f"Grid-ul {grid_mgmt.ROMGEO_GRID_VER} selectat.")
    except:
        raise Exception('No Grid available.')

    #set combo if dev mode and multigrid
    if hasattr(window.ui,'combo_info_center'):
        index = window.ui.combo_info_center.findText(grid_mgmt.ROMGEO_GRID_FILE.name)
        if index >= 0:
            window.ui.combo_info_center.setCurrentIndex(index)
            
def hide_splash():
    if pyi_splash:
        pyi_splash.close()




def main():

    set_log_level(config.LOGLEVEL)

    try:
        load_config_overrides(grid_mgmt.ROMGEO_APPDATA / 'config.ini')
        load_config_settings (grid_mgmt.ROMGEO_APPDATA / 'config.ini')
    except:
        pass

    set_log_level(config.LOGLEVEL)

    # Create Main Window
    app = QApplication(sys.argv)
    window = RomgeoTableConvertApp()
    window.show()

    window.ui.actionSetari_aplicatie.setEnabled(False)

    import random
    window.ui.label_info_left.setPixmap(QPixmap(f":/logo/images/logo-{random.randint(0, 3)}.png"))

    exevers = _get_exe_version()
    win_title = f"{window.windowTitle()}{' [DEV-MODE]' if config.DEV else ''} [vers. {exevers or config.EXE_VERSION}]"
    window.setWindowTitle(win_title)

    ## Set Developer Mode
    enable_developer_mode(window)
   
    ## Auto update
    check_grid_git_updates()

    ## check Pre-release
    pre_release_text = check_grid_git_prerelease()

    # Set GRID Release/pre-release labels
    window.ui.label_info_center.setText(f"<html><head/><body><p><span style=\" font-size:10pt;\">Versiune GRID: {grid_mgmt.ROMGEO_GRID_VER}{pre_release_text}</span></p></body></html>")

    ## Set current grid
    select_grid(window)
    
    # Hide the PyInstaller splash once GUI is ready
    hide_splash()

    ## Check exe update
    check_exe_update(window)

    sys.exit(app.exec_())




if __name__ == "__main__":
    main()
