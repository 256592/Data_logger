"""
Dialog pro import CSV souboru.

"""

import csv
import io
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QSizePolicy, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QColor


# ---------------------------------------------------------------------------
# Drag & drop zóna
# ---------------------------------------------------------------------------

class _DropZone(QFrame):
    """Plocha pro drag & drop nebo kliknutí pro výběr souboru."""

    file_selected = pyqtSignal(str)   # cesta k souboru

    _STYLE_NORMAL = """
        QFrame {
            border: 2px dashed #aaaaaa;
            border-radius: 8px;
            background: #f8f8f8;
        }
    """
    _STYLE_HOVER = """
        QFrame {
            border: 2px dashed #4a90d9;
            border-radius: 8px;
            background: #eaf4ff;
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setStyleSheet(self._STYLE_NORMAL)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self._text_label = QLabel("Drag and drop the CSV file \nor click to select")
        self._text_label.setFont(QFont("Segoe UI", 11))
        self._text_label.setAlignment(Qt.AlignCenter)

        self._text_label.setStyleSheet("border: none;")
        layout.addWidget(self._text_label)
        self.setLayout(layout)

    # --- drag & drop ---

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".csv") for u in urls):
                event.acceptProposedAction()
                self.setStyleSheet(self._STYLE_HOVER)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._STYLE_NORMAL)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self._STYLE_NORMAL)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".csv"):
                self.file_selected.emit(path)
                return

    # --- kliknutí ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select CSV file", "", "CSV files (*.csv);;All files (*)"
            )
            if path:
                self.file_selected.emit(path)

    def set_filename(self, name: str):
        self._text_label.setText(f"{name}")
        self._text_label.setStyleSheet("color: #2a7a2a;")
        self._text_label.setStyleSheet("border: none;")

# Hlavní dialog

_SEPARATORS = {
    "Comma  ( , )": ",",
    "Semicolon  ( ; )": ";"
}

_PREVIEW_ROWS = 20

class CsvImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import CSV")
        self.setMinimumSize(700, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._filepath: str = ""
        self.headers: list[str] = []
        self.rows: list[list[str]] = []

        self._build_ui()

    # UI

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Drop zóna
        self._drop_zone = _DropZone()
        self._drop_zone.file_selected.connect(self._on_file_selected)
        layout.addWidget(self._drop_zone)

        # Oddělovač
        sep_layout = QHBoxLayout()
        sep_layout.addWidget(QLabel("Separator:"))
        self._sep_combo = QComboBox()
        self._sep_combo.setMinimumContentsLength(18)
        self._sep_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for label in _SEPARATORS:
            self._sep_combo.addItem(label)
        self._sep_combo.currentIndexChanged.connect(self._reload_preview)
        sep_layout.addWidget(self._sep_combo)
        sep_layout.addStretch()

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: red;")
        sep_layout.addWidget(self._status_label)
        layout.addLayout(sep_layout)

        # Náhledová tabulka
        self._preview_table = QTableWidget(0, 0)
        self._preview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._preview_table.setAlternatingRowColors(True)
        layout.addWidget(self._preview_table)

        # Tlačítka
        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self.setLayout(layout)

    # Logika načítání

    def _on_file_selected(self, path: str):
        self._filepath = path
        self._drop_zone.set_filename(path.split("/")[-1].split("\\")[-1])
        self._reload_preview()

    def _reload_preview(self):
        if not self._filepath:
            return
        sep = _SEPARATORS[self._sep_combo.currentText()]
        try:
            self.headers, self.rows = self._parse_csv(self._filepath, sep)
            self._fill_preview(self.headers, self.rows[:_PREVIEW_ROWS])
            self._status_label.setText("")
            self._buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        except Exception as e:
            self._status_label.setText(f"Error: {e}")
            self._buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    @staticmethod
    def _parse_csv(path: str, sep: str | None) -> tuple[list[str], list[list[str]]]:
        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
            f.seek(0)

            if sep is None:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
                reader = csv.reader(f, dialect)
            else:
                reader = csv.reader(f, delimiter=sep)

            all_rows = list(reader)

        if not all_rows:
            raise ValueError("File is empty.")

        headers = all_rows[0]
        rows = all_rows[1:]
        if len(headers) != 6:
            raise ValueError(
                "CSV file must contain exactly 6 columns."
            )

        for row in rows:
            if len(row) != 6:
                raise ValueError(
                    "The CSV file contains an invalid number of columns."
                )

        return headers, rows

    def _fill_preview(self, headers: list[str], rows: list[list[str]]):
        self._preview_table.clear()
        self._preview_table.setColumnCount(len(headers))
        self._preview_table.setRowCount(len(rows))
        self._preview_table.setHorizontalHeaderLabels(headers)

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._preview_table.setItem(r, c, item)

        self._preview_table.resizeColumnsToContents()


    # Potvrzení
    def _on_accept(self):
        sep = _SEPARATORS[self._sep_combo.currentText()]
        try:
            self.headers, self.rows = self._parse_csv(self._filepath, sep)
            self.accept()
        except Exception as e:
            self._status_label.setText(f"Error while loading: {e}")