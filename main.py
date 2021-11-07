import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPalette, QColor

from src.MainWindow import MainWindow


def prepare_palette() -> QPalette:
    """
    Dark colors palette.

    Returns
    -------
    QPalette
    """
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(43, 43, 43))
    palette.setColor(QPalette.Base, QColor(43, 43, 43).lighter())
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QPalette.Text, QtCore.Qt.white)
    palette.setColor(QPalette.WindowText, QtCore.Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QPalette.BrightText, QtCore.Qt.red)
    palette.setColor(QPalette.Highlight, QColor(47, 101, 202))
    palette.setColor(QPalette.HighlightedText, QtCore.Qt.white)
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor(15, 15, 15))
    return palette


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setPalette(prepare_palette())
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
