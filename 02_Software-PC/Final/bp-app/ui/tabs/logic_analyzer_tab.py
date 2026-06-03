"""
Logic Analyzer tab.

"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QStackedWidget,
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

from ui.widgets.plot_widget import LaPlotWidget


# --- Idle view ---

class _IdleView(QWidget):

    configure_requested = pyqtSignal()
    import_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(
            '<a href="configure">Configure</a> device and start recording ')

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

# --- Recording view ---

_CHECKBOX_STYLE = """
QCheckBox::indicator { width: 30px; height: 30px; }
QCheckBox { spacing: 2px; }
"""

_CHANNEL_LABELS = [
    "CH0", "CH1", "CH2", "CH3",
    "CH4", "CH5", "CH6", "CH7",
]


class _RecordingView(QWidget):

    export_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    run_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # UI

    def _build_ui(self):
        main_layout = QVBoxLayout()

        main_layout.addLayout(self._build_channel_info())
        main_layout.addWidget(self._build_plot(), stretch=1)

        self.setLayout(main_layout)

    def _build_channel_info(self) -> QGridLayout:
        grid = QGridLayout()


        self.sample_rate_label = QLabel("Sample rate: —")
        grid.addWidget(self.sample_rate_label, 0, 8)

        # Checkboxy
        self.run_stop_btn = QPushButton("Run")
        self.run_stop_btn.setCheckable(True)
        self.run_stop_btn.setChecked(False)
        self.run_stop_btn.clicked.connect(self._on_run_stop_clicked)
        grid.addWidget(self.run_stop_btn, 1, 8)

        return grid

    def _on_run_stop_clicked(self, checked: bool):
        if checked:
            self.run_stop_btn.setText("Stop")
            self.run_requested.emit()
        else:
            self.run_stop_btn.setText("Run")
            self.stop_requested.emit()

    def _build_plot(self) -> LaPlotWidget:
        self.plot_widget = LaPlotWidget()
        return self.plot_widget

    def update_sample_rate(self, rate: str):
        self.sample_rate_label.setText(f"Sample rate: {rate}")

    def update_sample_count(self, count: int):
        pass  # samples label odstraněn, metoda zachována pro zpětnou kompatibilitu

    def reset_run_stop(self):
        self.run_stop_btn.setChecked(False)
        self.run_stop_btn.setText("Run")

    def update_plot(self, samples: list[list[int]], rate_khz: float):
        self.plot_widget.set_sample_rate_khz(rate_khz)
        self.plot_widget.plot_data(samples)

# --- Logic Analyzer tab ---

class LogicAnalyzerTab(QWidget):

    recording_state_changed = pyqtSignal(bool)

    configure_requested = pyqtSignal()
    import_requested = pyqtSignal()
    export_requested = pyqtSignal()
    run_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    _IDX_IDLE = 0
    _IDX_RECORDING = 1

    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_recording = False

        self._build_ui()

    # --- UI ---

    def _build_ui(self):
        self._stack = QStackedWidget()

        # Idle view

        self._idle_view = _IdleView()

        self._idle_view.configure_requested.connect(
            self.configure_requested
        )

        self._idle_view.import_requested.connect(
            self.import_requested
        )

        # Recording view

        self._recording_view = _RecordingView()

        self._recording_view.export_requested.connect(
            self.export_requested
        )

        self._recording_view.run_requested.connect(
            self.run_requested
        )

        self._recording_view.stop_requested.connect(
            self.stop_requested
        )

        self._stack.addWidget(self._idle_view)
        self._stack.addWidget(self._recording_view)

        layout = QVBoxLayout()
        layout.addWidget(self._stack)

        self.setLayout(layout)

    # Přepínání stavů

    def start_recording(self):
        if self._is_recording:
            return

        self._is_recording = True

        self._recording_view.reset_run_stop()
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