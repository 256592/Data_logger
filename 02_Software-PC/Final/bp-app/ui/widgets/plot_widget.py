from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)  # ← přidej

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)  # ← přidej
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self._draw_placeholder()

        def _draw_placeholder(self):
            self.axes.plot([1, 2, 3], [1, 4, 2])
            self.axes.set_xlabel("Sample")
            self.axes.set_ylabel("Voltage [mV]")
            self.axes.grid(True)
            self.canvas.draw()

        def clear(self):
            self.axes.clear()
            self.canvas.draw()

        def plot(self, x, y, xlabel="Sample", ylabel="Voltage [mV]"):
            self.axes.clear()
            self.axes.plot(x, y)
            self.axes.set_xlabel(xlabel)
            self.axes.set_ylabel(ylabel)
            self.axes.grid(True)
            self.canvas.draw()

    def _draw_placeholder(self):
        self.axes.clear()  # ← přidej tento řádek
        self.axes.plot([1, 2, 3], [1, 4, 2])
        self.axes.set_xlabel("Sample")
        self.axes.set_ylabel("Voltage [mV]")
        self.axes.grid(True)
        self.canvas.draw()

    def clear(self):
        self.figure.clear()
        self.canvas.draw()

    def plot(self, x, y, xlabel="Sample", ylabel="Voltage [mV]"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(x, y)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)
        self.canvas.draw()

_CH_ORDER = [0, 2, 4, 6, 1, 3, 5, 7]

class LaPlotWidget(QWidget):
    # Graf pro Logic Analyzer — 8 kanálů nad sebou, vodorovná osa v sekundách

    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self._sample_period = 1.0
        self._axes = []
        self._draw_placeholder()

    def set_sample_rate_khz(self, rate_khz: float):
        if rate_khz > 0:
            self._sample_period = 1.0 / (rate_khz * 1000)

    def _draw_placeholder(self):
        self.figure.clear()
        self._axes = []
        for i in range(8):
            if i == 0:
                ax = self.figure.add_subplot(8, 1, 1)
            else:
                ax = self.figure.add_subplot(8, 1, i + 1, sharex=self._axes[0])
            ax.set_ylabel(f"CH{i}", rotation=0, labelpad=24, va="center")
            ax.set_yticks([])
            ax.grid(True, axis="x")
            if i < 7:
                ax.tick_params(labelbottom=False)
            self._axes.append(ax)
        self._axes[-1].set_xlabel("Time [s]")
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_data(self, samples: list[list[int]]):
        if not samples:
            return

        n = len(samples)
        t = [i * self._sample_period for i in range(n)]

        self.figure.clear()
        self._axes = []

        for ch in range(8):
            if ch == 0:
                ax = self.figure.add_subplot(8, 1, 1)
            else:
                ax = self.figure.add_subplot(8, 1, ch + 1, sharex=self._axes[0])
            y = [row[_CH_ORDER[ch]] for row in samples]
            ax.step(t, y, where="post", linewidth=2)
            ax.set_ylim(-0.2, 1.2)
            ax.set_yticks([])
            ax.set_ylabel(f"CH{ch}", rotation=0, labelpad=24, va="center")
            ax.grid(True, axis="x")
            if ch < 7:
                ax.tick_params(labelbottom=False)
            self._axes.append(ax)

        self._axes[-1].set_xlabel("Time [s]")
        self.figure.tight_layout()
        self.canvas.draw()

    def clear(self):
        self._draw_placeholder()