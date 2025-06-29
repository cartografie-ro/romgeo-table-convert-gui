from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QCheckBox
from PyQt5.QtCore import Qt

class InfoDialog(QDialog):
    def __init__(self, message: str, parent=None, align=Qt.AlignCenter):
        super().__init__(parent)
        self.setWindowTitle("Informații")
        self.setModal(True)
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout(self)

        # Info/help label
        self.label = QLabel(message)
        self.label.setAlignment(align)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        layout.addWidget(self.label)

        # Checkbox: don't show again
        self.checkbox = QCheckBox("Ascunde acest mesaj")
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button, alignment=Qt.AlignCenter)

    def should_hide_future(self) -> bool:
        return self.checkbox.isChecked()

