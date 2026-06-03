"""
Hlavní okno aplikace.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QApplication, QStyleFactory,
    QMessageBox, QProgressDialog, QPushButton
)
from PyQt5.QtCore import Qt

from ui.tabs.logic_analyzer_tab import LogicAnalyzerTab
from ui.tabs.data_logger_tab import DataLoggerTab
from ui.dialogs.configure_dialog import ConfigureDialog, DeviceConfig
from ui.dialogs.csv_import_dialog import CsvImportDialog
from core.hid_device import HidWorker, ConfigWorker, HidDevice, DEVICE_VID, DEVICE_PID, LaDataWorker, DlSampleWorker
import sys
import os
from PyQt5.QtCore import Qt, QTimer
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._device_config: DeviceConfig | None = None
        self._hid_device: HidDevice | None = None
        self._hid_worker: HidWorker | None = None
        self._cfg_worker: ConfigWorker | None = None
        self._progress: QProgressDialog | None = None

        self._setup_window()
        self._build_ui()
        self._connect_signals()

        self._la_worker: LaDataWorker | None = None
        self._la_samples: list[list[int]] = []
        os.makedirs(DATA_DIR, exist_ok=True)

        self._dl_timer: QTimer | None = None
        self._dl_samples: list[list[int]] = []

    # Inicializace okna

    def _setup_window(self):
        self.setWindowTitle("Logic Analyzer and Data Logger Manager")
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        self.showMaximized()

        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

    # Sestavení UI
    def _build_ui(self):

        top_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Restart")
        self.refresh_btn.clicked.connect(self._on_refresh)
        top_layout.addStretch()
        top_layout.addWidget(self.refresh_btn)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(True)

        self.logic_analyzer_tab = LogicAnalyzerTab()
        self.data_logger_tab = DataLoggerTab()

        self.tab_widget.addTab(self.logic_analyzer_tab, "Logic Analyzer")
        self.tab_widget.addTab(self.data_logger_tab, "Data Logger")

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.tab_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # Propojení signálů
    def _connect_signals(self):
        # Signály z Data Logger tab
        self.data_logger_tab.configure_requested.connect(self._on_configure_clicked)
        self.data_logger_tab.import_requested.connect(self._on_import)
        self.data_logger_tab.export_requested.connect(self._on_export)
        self.data_logger_tab.sample_requested.connect(self._on_dl_sample)
        self.data_logger_tab.dl_run_stop_requested.connect(self._on_dl_run_stop)

        # Signály z Logic Analyzer tab
        self.logic_analyzer_tab.configure_requested.connect(self._on_configure_clicked)
        self.logic_analyzer_tab.import_requested.connect(self._on_import)
        self.logic_analyzer_tab.export_requested.connect(self._on_export)
        self.logic_analyzer_tab.run_requested.connect(self._on_run)
        self.logic_analyzer_tab.stop_requested.connect(self._on_stop)

    # 1) klik Configure -> připojení k HID zařízení
    def _on_configure_clicked(self):
        # Spustí HidWorker — připojení a ping v pozadí.
        self._show_progress("Connecting the device…", self._cancel_hid_worker)
        print("Connecting the device…")
        self._hid_worker = HidWorker(vid=DEVICE_VID, pid=DEVICE_PID, parent=self)
        self._hid_worker.connected.connect(self._on_device_connected)
        self._hid_worker.error.connect(self._on_device_error)
        self._hid_worker.finished.connect(self._hide_progress)
        self._hid_worker.start()

    def _cancel_hid_worker(self):
        if self._hid_worker and self._hid_worker.isRunning():
            self._hid_worker.terminate()
            self._hid_worker.wait()

    # 2a) zařízení odpovědělo -> otevři dialog
    def _on_device_connected(self, device: HidDevice):
        self._hid_device = device
        self._open_configure_dialog()

    def _open_configure_dialog(self):
        dialog = ConfigureDialog(current_config=self._device_config, parent=self)
        if dialog.exec() == ConfigureDialog.Accepted:
            self._device_config = dialog.config
            self._send_config(self._device_config)

    # 2b) zařízení nenalezeno
    def _on_device_error(self, message: str):
        QMessageBox.critical(self, "Error while connecting", message)

    # 3) odeslání konfigurace -> ConfigWorker
    def _send_config(self, cfg: DeviceConfig):
        if self._hid_device is None:
            self._apply_config(cfg)
            return

        self._show_progress("Sending configuration…", self._cancel_cfg_worker)

        self._cfg_worker = ConfigWorker(self._hid_device, cfg, parent=self)
        self._cfg_worker.success.connect(self._on_config_sent)
        self._cfg_worker.error.connect(self._on_config_error)
        self._cfg_worker.finished.connect(self._hide_progress)
        self._cfg_worker.start()

    def _cancel_cfg_worker(self):
        if self._cfg_worker and self._cfg_worker.isRunning():
            self._cfg_worker.terminate()
            self._cfg_worker.wait()

    # 4a) ACK -> spustí recording

    def _on_config_sent(self):
        self._apply_config(self._device_config)

    # 4b) ERR od zařízení

    def _on_config_error(self, message: str):
        QMessageBox.critical(self, "Configuration error", message)

    def _on_dl_sample(self):
        if self._hid_device:
            worker = DlSampleWorker(self._hid_device, parent=self)
            worker.sample_received.connect(self._on_dl_packet)
            worker.start()

    def _on_dl_packet(self, channels: list[int]):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[DL] CH0={channels[0]} CH1={channels[1]} CH2={channels[2]} CH3={channels[3]}")

        if not hasattr(self, '_dl_samples'):
            self._dl_samples = []
        self._dl_samples.append(channels)

        self.data_logger_tab.recording_view.update_live_data(self._dl_samples, now)

        # zápis do CSV
        dl_log = os.path.join(DATA_DIR, "dl_log.csv")
        if not os.path.exists(dl_log):
            ch_names = [ch.name for ch in self._device_config.channels]
            with open(dl_log, "w") as f:
                f.write("#,Time," + ",".join(ch_names) + "\n")

        with open(dl_log, "a") as f:
            idx = len(self._dl_samples)
            f.write(f"{idx},{now}," + ",".join(map(str, channels)) + "\n")

    def _on_dl_run_stop(self, running: bool):
        if self._hid_device:
            if running:
                self._start_dl_auto()
            else:
                self._stop_dl_auto()

    def _start_dl_auto(self):
        period_ms = self._device_config.log_period_s * 1000
        self._dl_timer = QTimer(self)
        self._dl_timer.setInterval(period_ms)
        self._dl_timer.timeout.connect(self._on_dl_sample)
        self._dl_timer.start()

    def _stop_dl_auto(self):
        if self._dl_timer:
            self._dl_timer.stop()
            self._dl_timer = None

    def _on_run(self):
        if self._hid_device:
            self._hid_device.send_la_run()

    def _on_stop(self):
        if self._hid_device:
            self._hid_device.send_la_stop()
            self._la_samples = []
            self._la_worker = LaDataWorker(self._hid_device, parent=self)
            self._la_worker.packet_received.connect(self._on_la_packet)
            self._la_worker.finished_capture.connect(self._on_la_finished)
            self._la_worker.start()

    def _on_la_packet(self, pkt):
        for byte in pkt.la_payload:
            bits = [(byte >> i) & 1 for i in range(8)]
            self._la_samples.append(bits)

    def _on_la_finished(self):
        rate_khz = self._device_config.sample_rate_khz if self._device_config else 1.0
        self.logic_analyzer_tab.recording_view.update_plot(self._la_samples, rate_khz)

    # Konfigurace + přepnutí UI do záznamu

    def _apply_config(self, cfg: DeviceConfig):
        self.data_logger_tab.stop_recording()
        self.logic_analyzer_tab.stop_recording()

        if cfg.device_mode == "Data Logger":
            if cfg.logger_mode == "Remote":
                QMessageBox.information(
                    self, "Configuration sent",
                    "Confuguration successfully sent to device."
                )
                return

            dl = self.data_logger_tab
            dl.recording_view.update_sample_rate(f"{cfg.log_period_s} s")
            dl.recording_view.update_sample_count(0)
            self.tab_widget.setCurrentWidget(dl)
            dl.start_recording(cfg.logger_mode)
            dl_log = os.path.join(DATA_DIR, "dl_log.csv")
            if os.path.exists(dl_log):
                os.remove(dl_log)
            self._dl_samples = []
        else:
            la = self.logic_analyzer_tab
            la.recording_view.update_sample_rate(f"{cfg.sample_rate_khz} kHz")
            la.recording_view.update_sample_count(0)
            self.tab_widget.setCurrentWidget(la)
            la.start_recording()

    # Import / Export CSV

    def _on_import(self):
        import shutil
        dialog = CsvImportDialog(parent=self)
        if dialog.exec() == CsvImportDialog.Accepted:
            dest = os.path.join(DATA_DIR, "dl_import.csv")
            shutil.copy2(dialog._filepath, dest)

            dl = self.data_logger_tab
            self.tab_widget.setCurrentWidget(dl)
            if not dl.is_recording:
                dl.start_recording()
            dl.recording_view.load_csv_data(dialog.headers, dialog.rows)

    def _on_export(self):
        from PyQt5.QtWidgets import QFileDialog
        import shutil
        import os

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        source = os.path.join(BASE_DIR, "..", "..", "data", "dl_import.csv")

        if not os.path.exists(source):
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV files (*.csv)"
        )
        if not path:
            return

        if not path.endswith(".csv"):
            path += ".csv"

        shutil.copy2(source, path)

    # Progress dialog

    def _show_progress(self, message: str, cancel_callback):
        self._progress = QProgressDialog(message, "Cancel", 0, 0, self)
        self._progress.setWindowTitle("Wait")
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setMinimumDuration(0)
        self._progress.canceled.connect(cancel_callback)
        self._progress.show()

    def _hide_progress(self):
        if self._progress:
            self._progress.close()
            self._progress = None

    # Zavření okna

    def closeEvent(self, event):
        self._cancel_hid_worker()
        self._cancel_cfg_worker()
        if self._hid_device:
            self._hid_device.close()
        event.accept()
        if self._la_worker and self._la_worker.isRunning():
            self._la_worker.stop()
            self._la_worker.wait()

    def _on_refresh(self):
        self._cancel_hid_worker()
        self._cancel_cfg_worker()
        if self._hid_device:
            self._hid_device.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)