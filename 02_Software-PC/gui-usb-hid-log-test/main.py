import sys
import hid
import csv
import os
import datetime
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import (QApplication, QDialog, QGridLayout, QLabel, QPushButton, QSpinBox, QStyleFactory,
                             QTableWidget, QTabWidget, QWidget, QVBoxLayout, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, pyqtSignal
# from PyQt5.QtWidgets.QMainWindow import closeEvent

VENDOR_ID = 0x1FC9
PRODUCT_ID = 0x0081
CSV_FILE = "hid_log.csv"
report_length = 64

# HID message:
# 1st Byte: auto 0000 0001, manual 0000 0010, stop 0000 0000
# 2nd Byte: logging period in range 1-128 (in vals to transmit 0-127, 1 Byte)

# --- HID device ---
device = None
device_connected = False

def connect_hid():
    global device
    global device_connected
    try:
        device = hid.device()
        device.open(VENDOR_ID, PRODUCT_ID)
        print("HID device connected.")
        device_connected = True
    except Exception as e:
        print("Error when connecting HID device:", e)
        device = None
        device_connected = False
    # print(device_connected)

    return device_connected

# --- CSV ---
def init_csv():
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Value"])  # header

def clear_csv():
    if os.path.isfile(CSV_FILE):
        open(CSV_FILE, mode='w').close()  # open and close -> file cleared
        print("CSV is clear")
        with open(CSV_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Value"])  # header

def log_to_csv(val):
    print("Logging to CSV:", val)  # check
    file_exists = os.path.isfile(CSV_FILE)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Time", "Value"])
        writer.writerow([now, int(val, 16)])

def transmit_message(report):
    if device is None:
        print("Device disconnected.")
        return
    message = b"\xAA" + bytes(report)
    try:
        device.write(message)
        print("Transmitted:", message)
    except Exception as e:
        print("Error while transmitting:", e)

class HidWorker(QObject):
    data_received = pyqtSignal(bytes)
    finished = pyqtSignal()

    def __init__(self, vendor_id, product_id):
        super().__init__()
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.running = True

    @pyqtSlot() # nevim co to dela, ale funguje to i bez toho
    def run(self):
        device = hid.device()
        device.open(self.vendor_id, self.product_id)
        device.set_nonblocking(False)

        while self.running:
            dataAll = device.read(64)  # velikost reportu
            data = dataAll[0:1]
            if data:
                self.data_received.emit(bytes(data))

    def stop(self):
        self.running = False

class Widgets(QDialog):
    def __init__(self, parent=None):
        super(Widgets, self).__init__(parent)

        init_csv()

        # Create thread
        self.thread = QThread()
        self.worker = HidWorker(0x1FC9, 0x0081)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        # Create widgets
        self.createModeTabWidget()
        self.connectBtn = QPushButton("Connect device")
        self.connectBtn.clicked.connect(self.startReadingHid)

        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.connectBtn)
        mainLayout.addWidget(self.modeTabWidget)
        self.setLayout(mainLayout)

        self.setWindowTitle("Data Logger Manager")
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        self.originalPalette = QApplication.palette()
        self.resize(700, 800)

    def createAutoModeTab(self):
        tab = QWidget()
        layout = QGridLayout()

        self.spinBox = QSpinBox()
        self.spinBox.setValue(1)
        self.spinBox.setRange(1, 128)
        self.spinBox.valueChanged.connect(self.updateSecsVal)

        self.tableA = QTableWidget()

        self.toggleBtn = QPushButton("Run")
        self.toggleBtn.setCheckable(True)
        self.toggleBtn.clicked.connect(self.runAutoLogging)

        title = QLabel("Automatic logging")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))

        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(QLabel("Set sample period [sec]:"), 1, 0)
        layout.addWidget(self.spinBox, 1, 1)
        layout.addWidget(self.toggleBtn, 1, 2)
        layout.addWidget(self.tableA, 2, 0, 1, 3)

        tab.setLayout(layout)
        self.load_csv(self.tableA)
        return tab

    def createManualModeTab(self):
        tab = QWidget()
        layout = QGridLayout()

        self.tableB = QTableWidget(10, 10)
        self.btn = QPushButton("Log")
        self.btn.clicked.connect(self.sendLog)

        title = QLabel("Manual logging")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))

        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(QLabel("Click to make a log:"), 1, 0)
        layout.addWidget(self.btn, 1, 1)
        layout.addWidget(self.tableB, 2, 0, 1, 2)

        tab.setLayout(layout)
        self.load_csv(self.tableB)
        return tab

    def createModeTabWidget(self):
        self.modeTabWidget = QTabWidget()
        self.modeTabWidget.addTab(self.createAutoModeTab(), "Auto mode")
        self.modeTabWidget.addTab(self.createManualModeTab(), "Manual mode")

    def runAutoLogging(self):
        if self.toggleBtn.isChecked():
            report = [0] * 64
            report[0] = 1
            report[1] = self.updateSecsVal()
            # print(bytes(report))
            transmit_message(report)
        else:
            report = [0] * 64
            report[0] = 0
            report[1] = 0
            # print(bytes(report))
            transmit_message(report)

    def sendLog(self):
        report = [0] * 64
        report[0] = 2
        # print(bytes(report))
        transmit_message(report)

    def updateSecsVal(self):
        return self.spinBox.value()-1

    def load_csv(self, table):
        try:
            with open(CSV_FILE, newline='') as f:
                reader = list(csv.reader(f))
        except FileNotFoundError:
            reader = []

        if not reader:
            table.setRowCount(0)
            table.setColumnCount(0)
            return

        table.setRowCount(len(reader) - 1)
        table.setColumnCount(len(reader[0]))
        table.setHorizontalHeaderLabels(reader[0])  # header

        for row_idx, row in enumerate(reader[1:]):  # přeskočit header
            for col_idx, val in enumerate(row):
                table.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def on_hid_data(self, data):
        # print(data.hex())
        log_to_csv(data.hex())
        self.load_csv(self.tableA)
        self.tableA.resizeColumnsToContents()
        # self.tableA.resizeRowsToContents()
        self.tableA.scrollToBottom()

        self.load_csv(self.tableB)
        self.tableB.resizeColumnsToContents()
        # self.tableB.resizeRowsToContents()
        self.tableB.scrollToBottom()

    def closeEvent(self, event):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()

    def startReadingHid(self):

        if device_connected == False:
            connect_hid()
            # --- HID read ---
            self.worker.data_received.connect(self.on_hid_data)
            self.worker.finished.connect(self.thread.quit)
            self.connectBtn.setText("Disconnect device")
        elif device_connected:
            self.device_connected = False
            print("HID device disconnected")
            self.worker.data_received.disconnect(self.on_hid_data)
            self.connectBtn.setText("Connect device")

if __name__ == '__main__':
    clear_csv()
    app = QApplication(sys.argv)
    gallery = Widgets()
    gallery.show()
    sys.exit(app.exec())