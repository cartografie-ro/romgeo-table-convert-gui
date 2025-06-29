import sys
import time

try:
    import pyi_splash
    pyi_splash.update_text("Loading RomGEO Table Convert GUI...")
except ImportError:
    pyi_splash = None



from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RomGEO Demo")
        self.setGeometry(200, 200, 600, 400)
        label = QLabel("App is ready!", self)
        label.setGeometry(200, 180, 200, 40)

def main():
    app = QApplication(sys.argv)

    window = DemoWindow()
    window.show()
    time.sleep(10)

    # Hide the PyInstaller splash once GUI is ready
    if pyi_splash:
        pyi_splash.update_text("Loading RomGEO Table Convert GUI...")
        time.sleep(3)
        pyi_splash.close()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
