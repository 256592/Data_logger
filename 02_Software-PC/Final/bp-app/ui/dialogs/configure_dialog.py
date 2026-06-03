"""
Konfigurační dialog
"""
from dataclasses import dataclass, field
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QWidget, QRadioButton, QButtonGroup,
)
from PyQt5.QtCore import Qt

@dataclass
class ChannelConfig:
    enabled: bool = True
    name: str = ""
    signal_type: str = "Analog"


@dataclass
class DeviceConfig:
    device_mode: str = "Data Logger"
    logger_mode: str = "Real-time Auto"

    sample_rate_khz: int = 1000

    # Data logger
    log_period_s: int = 1
    log_duration_s: int = 1

    # Logic Analyzer
    la_limited: bool = False
    la_duration_s: int = 10
    la_voltage: str = "3V3"

    channels: list = field(default_factory=lambda: [ChannelConfig() for _ in range(4)])

_SIGNAL_TYPES = ["Analog", "Digital"]   # Neimplementováno


class _ChannelRow(QWidget):

    def __init__(self, index: int, cfg: ChannelConfig, row_mode: str = "realtime", parent=None):
        super().__init__(parent)
        self._row_mode = row_mode

        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(cfg.enabled)

        self.name_edit = QLineEdit(cfg.name or f"CH{index}")
        self.name_edit.setMinimumWidth(100)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel(f"CH{index}"))
        layout.addWidget(self.enable_cb)

        if row_mode != "remote":
            layout.addWidget(QLabel("Title:"))
            layout.addWidget(self.name_edit)

        layout.addStretch()
        self.setLayout(layout)

        self._type_combo = None

        self.enable_cb.toggled.connect(self._on_toggle)
        self._on_toggle(cfg.enabled)

    def _on_toggle(self, enabled: bool):
        self.name_edit.setEnabled(enabled)

        if self._type_combo:
            self._type_combo.setEnabled(enabled)

    def get_config(self) -> ChannelConfig:
        return ChannelConfig(
            enabled=self.enable_cb.isChecked(),
            name=self.name_edit.text(),
            signal_type=self._type_combo.currentText() if self._type_combo else "Analog",
        )

# --- Dialog ---

_SAMPLE_RATES = [10, 20, 50, 100]

_DEVICE_MODES = ["Data Logger", "Logic Analyzer"]

_LOGGER_MODES = [
    "Real-time Auto",
    "Real-time Manual",
    "Remote",
]


class ConfigureDialog(QDialog):
    def __init__(self, current_config: DeviceConfig | None = None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configure device")
        self.setMinimumWidth(580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._cfg = current_config or DeviceConfig()
        self._channel_rows: list[_ChannelRow] = []

        self._build_ui()
        self._update_mode_visibility(self._cfg.device_mode)

    # --- UI ---

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(self._build_mode_group())
        layout.addWidget(self._build_sampling_group())

        self._channels_group = self._build_channels_group(
            self._channel_mode_for(self._cfg.logger_mode)
        )

        layout.addWidget(self._channels_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

    # --- Režim ---

    def _build_mode_group(self) -> QGroupBox:
        group = QGroupBox("Device mode")

        layout = QGridLayout()
        layout.setColumnMinimumWidth(0, 160)
        layout.setColumnStretch(1, 1)

        layout.addWidget(QLabel("Type:"), 0, 0)

        self.device_mode_combo = QComboBox()
        self.device_mode_combo.setMinimumContentsLength(18)
        self.device_mode_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        for m in _DEVICE_MODES:
            self.device_mode_combo.addItem(m)

        self.device_mode_combo.setCurrentText(self._cfg.device_mode)
        self.device_mode_combo.currentTextChanged.connect(self._update_mode_visibility)

        layout.addWidget(self.device_mode_combo, 0, 1)

        self._logger_mode_label = QLabel("Logger state:")

        self.logger_mode_combo = QComboBox()
        self.logger_mode_combo.setMinimumContentsLength(18)
        self.logger_mode_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        for m in _LOGGER_MODES:
            self.logger_mode_combo.addItem(m)

        self.logger_mode_combo.setCurrentText(self._cfg.logger_mode)
        self.logger_mode_combo.currentTextChanged.connect(self._on_logger_mode_changed)

        layout.addWidget(self._logger_mode_label, 1, 0)
        layout.addWidget(self.logger_mode_combo, 1, 1)

        group.setLayout(layout)

        return group

    # --- Vzorkování ---

    def _build_sampling_group(self) -> QGroupBox:
        group = QGroupBox("Sampling")

        layout = QGridLayout()
        layout.setColumnMinimumWidth(0, 160)
        layout.setColumnStretch(1, 1)

        # --- Vzorkovací frekvence ---

        self._sample_rate_label = QLabel("Sampling rate:")

        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.setMinimumContentsLength(14)
        self.sample_rate_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        for r in _SAMPLE_RATES:
            self.sample_rate_combo.addItem(f"{r} kHz", r)

        idx = min(
            range(len(_SAMPLE_RATES)),
            key=lambda i: abs(_SAMPLE_RATES[i] - self._cfg.sample_rate_khz)
        )

        self.sample_rate_combo.setCurrentIndex(idx)

        layout.addWidget(self._sample_rate_label, 0, 0)
        layout.addWidget(self.sample_rate_combo, 0, 1)

        self._voltage_label = QLabel("Logic level:")
        self._rb_3v3 = QRadioButton("3V3")
        self._rb_5v = QRadioButton("5V")
        self._voltage_group = QButtonGroup()
        self._voltage_group.addButton(self._rb_3v3)
        self._voltage_group.addButton(self._rb_5v)
        if self._cfg.la_voltage == "5V":
            self._rb_5v.setChecked(True)
        else:
            self._rb_3v3.setChecked(True)
        voltage_row = QHBoxLayout()
        voltage_row.addWidget(self._rb_3v3)
        voltage_row.addWidget(self._rb_5v)
        voltage_row.addStretch()
        layout.addWidget(self._voltage_label, 1, 0)
        layout.addLayout(voltage_row, 1, 1)

        # --- Perioda logování ---

        self._period_label = QLabel("Sampling period:")

        self.period_spin = QSpinBox()
        self.period_spin.setRange(1, 60)
        self.period_spin.setValue(
            min(max(self._cfg.log_period_s, 1), 60))
        self.period_spin.setSuffix(" s")
        self.period_spin.setMinimumWidth(140)

        period_row = QHBoxLayout()
        period_row.addWidget(self.period_spin)
        period_row.addStretch()

        layout.addWidget(self._period_label, 1, 0)
        layout.addLayout(period_row, 1, 1)

        # --- Doba logování (Remote) ---

        self._duration_label = QLabel("Session duration:")

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 168)
        self.duration_spin.setValue(
            min(max(self._cfg.log_duration_s, 1), 168)
        )
        self.duration_spin.setSuffix(" h")
        self.duration_spin.setMinimumWidth(140)

        duration_row = QHBoxLayout()
        duration_row.addWidget(self.duration_spin)
        duration_row.addStretch()

        layout.addWidget(self._duration_label, 2, 0)
        layout.addLayout(duration_row, 2, 1)

        group.setLayout(layout)

        return group

    # --- Kanály ---

    def _build_channels_group(self, channel_mode: str) -> QGroupBox:
        group = QGroupBox("Channesl configuration")

        layout = QVBoxLayout()

        self._channel_rows = []

        for i, ch_cfg in enumerate(self._cfg.channels):
            row = _ChannelRow(i, ch_cfg, row_mode=channel_mode)

            self._channel_rows.append(row)
            layout.addWidget(row)

        group.setLayout(layout)

        return group


    @staticmethod
    def _channel_mode_for(logger_mode: str) -> str:
        return "remote" if logger_mode == "Remote" else "realtime"

    # --- Handlery ---

    def _update_mode_visibility(self, device_mode: str):
        is_logger = (device_mode == "Data Logger")

        # Logic Analyzer only
        self._sample_rate_label.setVisible(not is_logger)
        self.sample_rate_combo.setVisible(not is_logger)
        show_voltage = not is_logger
        self._voltage_label.setVisible(show_voltage)
        self._rb_3v3.setVisible(show_voltage)
        self._rb_5v.setVisible(show_voltage)

        # Logger only
        self._logger_mode_label.setVisible(is_logger)
        self.logger_mode_combo.setVisible(is_logger)
        self._channels_group.setVisible(is_logger)

        logger_mode = self.logger_mode_combo.currentText()

        is_auto = is_logger and logger_mode == "Real-time Auto"
        is_remote = is_logger and logger_mode == "Remote"

        # Perioda logování
        self._period_label.setVisible(is_auto or is_remote)
        self.period_spin.setVisible(is_auto or is_remote)

        # Doba logování
        self._duration_label.setVisible(is_remote)
        self.duration_spin.setVisible(is_remote)

        self.adjustSize()

    def _on_logger_mode_changed(self, logger_mode: str):
        is_auto = (logger_mode == "Real-time Auto")
        is_remote = (logger_mode == "Remote")

        self._voltage_label.setVisible(False)
        self._rb_3v3.setVisible(False)
        self._rb_5v.setVisible(False)

        # Perioda
        self._period_label.setVisible(is_auto or is_remote)
        self.period_spin.setVisible(is_auto or is_remote)

        # Doba
        self._duration_label.setVisible(is_remote)
        self.duration_spin.setVisible(is_remote)

        self._rebuild_channels(logger_mode)

    def _rebuild_channels(self, logger_mode: str):
        new_mode = self._channel_mode_for(logger_mode)

        saved = [row.get_config() for row in self._channel_rows]

        main_layout = self.layout()

        old_idx = main_layout.indexOf(self._channels_group)

        self._channels_group.setParent(None)

        self._cfg = DeviceConfig(
            device_mode=self.device_mode_combo.currentText(),
            logger_mode=logger_mode,
            sample_rate_khz=self._cfg.sample_rate_khz,
            log_period_s=self._cfg.log_period_s,
            log_duration_s=self._cfg.log_duration_s,
            la_limited=self._cfg.la_limited,
            la_duration_s=self._cfg.la_duration_s,
            la_voltage="5V" if self._rb_5v.isChecked() else "3V3",
            channels=saved,
        )

        self._channels_group = self._build_channels_group(new_mode)

        main_layout.insertWidget(old_idx, self._channels_group)

        self.adjustSize()

    # --- Konfigurace ---

    @property
    def config(self) -> DeviceConfig:
        return DeviceConfig(
            device_mode=self.device_mode_combo.currentText(),
            logger_mode=self.logger_mode_combo.currentText(),
            sample_rate_khz=self.sample_rate_combo.currentData(),
            log_period_s=self.period_spin.value(),
            log_duration_s=self.duration_spin.value(),
            la_voltage="5V" if self._rb_5v.isChecked() else "3V3",
            channels=[row.get_config() for row in self._channel_rows],
        )