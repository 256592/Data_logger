import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

#debug
import faulthandler
faulthandler.enable()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()