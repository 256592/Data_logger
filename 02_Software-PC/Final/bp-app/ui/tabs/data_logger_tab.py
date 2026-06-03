"""
Data Logger tab.

"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QTableWidget, QStackedWidget, QTableWidgetItem
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets.plot_widget import PlotWidget


# --- Idle view (před záznamem) ---

class _IdleView(QWidget):

    # Signály pro akce
    configure_requested = pyqtSignal()
    import_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(
            '<a href="configure">Configure</a> device and start recording '
            'or <a href="import">import CSV file</a>'
        )
        title.setFont(QFont("Segoe UI", 16))
        title.setAlignment(Qt.AlignCenter)
        title.setTextFormat(Qt.RichText)
        title.setTextInteractionFlags(Qt.TextBrowserInteraction)
        title.setOpenExternalLinks(False)
        title.linkActivated.connect(self._on_link)

        layout.addWidget(title)
        self.setLayout(layout)

    def _on_link(self, link: str):
        if link == "configure":
            self.configure_requested.emit()
        elif link == "import":
            self.import_requested.emit()


# --- Recording view  (živý záznam) ---

_CHECKBOX_STYLE = """
QCheckBox::indicator { width: 30px; height: 30px; }
QCheckBox { spacing: 2px; }
"""

_STAT_STYLE = "border: 1px solid gray; padding: 5px;"

_CHANNEL_LABELS = ["CH0", "CH1", "CH2", "CH3"]
_STAT_LABELS = ["Average", "MIN", "MAX"]


class _RecordingView(QWidget):
    #tabulka + graf + statistiky

    export_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    sample_requested = pyqtSignal()
    dl_run_stop_requested = pyqtSignal(bool)  # True = run, False = stop

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # UI

    def _build_ui(self):
        main_layout = QHBoxLayout()

        self.preview_table = QTableWidget(0, 6)
        main_layout.addWidget(self.preview_table, 1)

        right_layout = QVBoxLayout()

        self._channel_info_widget = QWidget()
        self._channel_info_widget.setLayout(self._build_channel_info())
        right_layout.addWidget(self._channel_info_widget)
        right_layout.addWidget(self._build_plot(), stretch=4)
        right_layout.addLayout(self._build_stats_grid())

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 2)

        self.setLayout(main_layout)

    def _build_channel_info(self) -> QGridLayout:
        grid = QGridLayout()

        # Názvy kanálů + info nahoře
        for col, name in enumerate(_CHANNEL_LABELS):
            grid.addWidget(QLabel(name), 0, col)
        self.sample_rate_label = QLabel("Sample rate: —")
        grid.addWidget(self.sample_rate_label, 0, 4)

        # Checkboxy + info dole
        self.channel_checks: list[QCheckBox] = []
        for col in range(len(_CHANNEL_LABELS)):
            cb = QCheckBox()
            cb.setStyleSheet(_CHECKBOX_STYLE)
            cb.setChecked(True)
            cb.stateChanged.connect(
                self.update_plot_visibility
            )
            self.channel_checks.append(cb)
            grid.addWidget(cb, 1, col)

        self.samples_label = QLabel("Samples: —")
        grid.addWidget(self.samples_label, 1, 4)

        self.action_btn = QPushButton("")
        self.action_btn.setVisible(False)
        grid.addWidget(self.action_btn, 0, 5, 2, 1)

        return grid

    def _build_plot(self) -> PlotWidget:
        self.plot_widget = PlotWidget()
        return self.plot_widget

    def _build_stats_grid(self) -> QGridLayout:
        grid = QGridLayout()

        self.avg_label = QLabel("Average")
        self.min_label = QLabel("MIN")
        self.max_label = QLabel("MAX")

        for lbl in [self.avg_label, self.min_label, self.max_label]:
            lbl.setStyleSheet(_STAT_STYLE)

        grid.addWidget(self.avg_label, 0, 0)
        grid.addWidget(self.min_label, 0, 1)
        grid.addWidget(self.max_label, 1, 0)

        btn = QPushButton("Export CSV")
        btn.clicked.connect(self._on_export)
        grid.addWidget(btn, 1, 1)

        return grid


    # API pro aktualizaci dat

    def update_sample_rate(self, rate: str):
        if rate:
            self.sample_rate_label.setText(f"Sample rate: {rate}")
            self.sample_rate_label.setVisible(True)
        else:
            self.sample_rate_label.setVisible(False)

    def update_sample_count(self, count: int):
        self.samples_label.setText(f"Samples: {count}")

    def set_mode(self, mode: str):
        try:
            self.action_btn.clicked.disconnect()
        except Exception:
            pass

        if mode == "Real-time Manual":
            self.action_btn.setText("Take a sample")
            self.action_btn.setCheckable(False)
            self.action_btn.clicked.connect(self.sample_requested)
            self.action_btn.setVisible(True)
        elif mode == "Real-time Auto":
            self.action_btn.setText("Run")
            self.action_btn.setCheckable(True)
            self.action_btn.setChecked(False)
            self.action_btn.clicked.connect(self._on_dl_run_stop)
            self.action_btn.setVisible(True)
        else:
            self.action_btn.setVisible(False)

    def _on_dl_run_stop(self, checked: bool):
        if checked:
            self.action_btn.setText("Stop")
        else:
            self.action_btn.setText("Run")
        self.dl_run_stop_requested.emit(checked)

    def load_csv_data(self, headers: list[str], rows: list[list[str]]):
        self.update_sample_rate("")
        self.samples_label.setVisible(False)
        self.action_btn.setVisible(False)

        self.preview_table.clear()
        self.preview_table.setColumnCount(len(headers) + 1)
        self.preview_table.setRowCount(len(rows))
        self.preview_table.setHorizontalHeaderLabels(["#"] + headers)

        for r, row in enumerate(rows):
            self.preview_table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(r, c + 1, item)

        self.preview_table.resizeColumnsToContents()
        self.update_sample_rate("")
        self.plot_csv_data(rows)

    def plot_csv_data(self, rows):
        self.plot_widget.axes.clear()
        self.lines = []

        x_data = [float(row[0]) for row in rows]
        channel_cols = [2, 3, 4, 5]

        for i, col in enumerate(channel_cols):
            y_data = [float(row[col]) for row in rows]
            line, = self.plot_widget.axes.plot(
                x_data, y_data, label=_CHANNEL_LABELS[i]
            )
            self.lines.append(line)

        self.plot_widget.axes.set_xlabel("Time [s]")
        self.plot_widget.axes.set_ylabel("Voltage [mV]")
        self.plot_widget.axes.legend()
        self.plot_widget.axes.grid(True)
        self.plot_widget.canvas.draw()
        self._update_stats(rows)

    def update_plot_visibility(self):

        for i, line in enumerate(self.lines):
            line.set_visible(
                self.channel_checks[i].isChecked()
            )

        self.plot_widget.canvas.draw()

    def _update_stats(self, rows):
        channel_cols = [2, 3, 4, 5]
        avg_parts = []
        min_parts = []
        max_parts = []

        for i, col in enumerate(channel_cols):
            values = [float(row[col]) for row in rows if len(row) > col]
            if values:
                avg_parts.append(f"CH{i}: {sum(values) / len(values):.2f}")
                min_parts.append(f"CH{i}: {min(values):.2f}")
                max_parts.append(f"CH{i}: {max(values):.2f}")

        self.avg_label.setText("Average  " + "   ".join(avg_parts))
        self.min_label.setText("MIN  " + "   ".join(min_parts))
        self.max_label.setText("MAX  " + "   ".join(max_parts))

    def _on_export(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV files (*.csv)"
        )
        if not path:
            return

        if not path.endswith(".csv"):
            path += ".csv"

        # ulož aktuální data z tabulky
        rows = []
        for r in range(self.preview_table.rowCount()):
            row = []
            for c in range(self.preview_table.columnCount()):
                item = self.preview_table.item(r, c)
                row.append(item.text() if item else "")
            rows.append(row)

        headers = []
        for c in range(self.preview_table.columnCount()):
            headers.append(self.preview_table.horizontalHeaderItem(c).text())

        with open(path, "w") as f:
            f.write(",".join(headers) + "\n")
            for row in rows:
                f.write(",".join(row) + "\n")

    def update_live_data(self, all_samples: list[list[int]], timestamp: str = ""):
        self.plot_widget.axes.clear()
        self.lines = []

        # výpočet statistik
        avg_parts = []
        min_parts = []
        max_parts = []

        for i in range(4):
            values = [row[i] for row in all_samples]
            if values:
                avg_parts.append(f"CH{i}: {sum(values) / len(values):.2f}")
                min_parts.append(f"CH{i}: {min(values):.2f}")
                max_parts.append(f"CH{i}: {max(values):.2f}")

        self.avg_label.setText("Average  " + "   ".join(avg_parts))
        self.min_label.setText("MIN  " + "   ".join(min_parts))
        self.max_label.setText("MAX  " + "   ".join(max_parts))

        # inicializace tabulky
        if self.preview_table.columnCount() != 6 or self.preview_table.horizontalHeaderItem(0) is None:
            self.preview_table.setColumnCount(6)
            self.preview_table.setHorizontalHeaderLabels(["#", "Time"] + _CHANNEL_LABELS)
            self.preview_table.setRowCount(0)

        if not all_samples:
            self.plot_widget.canvas.draw()
            return

        x_data = list(range(len(all_samples)))

        for i in range(4):
            y_data = [row[i] for row in all_samples]
            line, = self.plot_widget.axes.plot(
                x_data, y_data, label=_CHANNEL_LABELS[i]
            )
            self.lines.append(line)

        self.plot_widget.axes.set_xlabel("Samples")
        self.plot_widget.axes.legend()
        self.plot_widget.axes.grid(True)
        self.plot_widget.canvas.draw()

        self.update_plot_visibility()

        # přidej poslední řádek do tabulky
        last = all_samples[-1]
        row_idx = self.preview_table.rowCount()
        self.preview_table.insertRow(row_idx)
        self.preview_table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
        self.preview_table.setItem(row_idx, 1, QTableWidgetItem(timestamp))
        for c, val in enumerate(last):
            item = QTableWidgetItem(str(val))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.preview_table.setItem(row_idx, c + 2, item)
        self.preview_table.scrollToBottom()
        self.update_sample_count(len(all_samples))
        self.preview_table.resizeColumnsToContents()



# --- Data Logger tab ---

class DataLoggerTab(QWidget):

    # Informuje MainWindow o změně
    recording_state_changed = pyqtSignal(bool)

    # Přeposílané signály pro MainWindow
    configure_requested = pyqtSignal()
    import_requested = pyqtSignal()
    export_requested = pyqtSignal()
    sample_requested = pyqtSignal()
    dl_run_stop_requested = pyqtSignal(bool)

    _IDX_IDLE = 0
    _IDX_RECORDING = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_recording = False
        self._build_ui()

    def _build_ui(self):
        self._stack = QStackedWidget()

        self._idle_view = _IdleView()
        self._idle_view.configure_requested.connect(self.configure_requested)
        self._idle_view.import_requested.connect(self.import_requested)

        self._recording_view = _RecordingView()
        self._recording_view.export_requested.connect(self.export_requested)
        self._recording_view.stop_requested.connect(self.stop_recording)
        self._recording_view.sample_requested.connect(self.sample_requested)
        self._recording_view.dl_run_stop_requested.connect(self.dl_run_stop_requested)

        self._stack.addWidget(self._idle_view)       # index 0
        self._stack.addWidget(self._recording_view)  # index 1

        layout = QVBoxLayout()
        layout.addWidget(self._stack)
        self.setLayout(layout)


    # Přepínání pohledů
    def start_recording(self, logger_mode: str = ""):
        if self._is_recording:
            return
        self._is_recording = True
        self._recording_view.set_mode(logger_mode)
        self._stack.setCurrentIndex(self._IDX_RECORDING)
        self.recording_state_changed.emit(True)

    def stop_recording(self):
        if not self._is_recording:
            return
        self._is_recording = False
        self._stack.setCurrentIndex(self._IDX_IDLE)
        self.recording_state_changed.emit(False)

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def recording_view(self) -> _RecordingView:
        return self._recording_view