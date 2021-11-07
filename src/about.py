from PyQt5 import uic
from PyQt5.QtWidgets import QDialog


class AboutWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/about.ui", self)
        self.buttonBox.clicked.connect(self.close)
