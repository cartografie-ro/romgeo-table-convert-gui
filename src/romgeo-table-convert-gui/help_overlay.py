from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class HelpOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SubWindow)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background-color: white;")

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        # Load image from compiled resource
        self.image = QPixmap(":/images/images/help_overlay.png")
        self.image_label.setPixmap(self.image)

    def resizeEvent(self, event):
        self.image_label.resize(self.size())

    def mousePressEvent(self, event):
        self.hide()
