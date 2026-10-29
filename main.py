from screen import Screen
from PyQt6 import QtWidgets
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = Screen()
    gui.show()
    app.exec()