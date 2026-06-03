"""
Komunikace zařízení přes USB HID.
"""

from __future__ import annotations
import time
import hid
from PyQt5.QtCore import QThread, pyqtSignal
import os

from core.protocol import make_ping, make_config, make_la_run, make_la_stop, Packet, RSP_PONG, RSP_ACK, RSP_ERR, make_ack, make_dl_sample_request, RSP_DL_DATA

DEVICE_VID = 0x1FC9
DEVICE_PID = 0x0081

PING_TIMEOUT_S   = 2.0
CONFIG_TIMEOUT_S = 3.0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

 #--- HidDevice ---

class HidDevice:

    def __init__(self):
        self._dev: hid.device | None = None

    # Připojení
    def connect(self, vid: int | None = None, pid: int | None = None) -> bool:
        self.close()
        try:
            self._dev = hid.device()
            self._dev.open(vid, pid)
            self._dev.set_nonblocking(True)
            return True
        except Exception:
            self._dev = None
            return False

    def close(self):
        if self._dev is not None:
            try:
                self._dev.close()
            except Exception:
                pass
            self._dev = None

    @property
    def is_open(self) -> bool:
        return self._dev is not None

    # TX
    def send_packet(self, pkt: bytearray) -> None:
        #assert len(pkt) == 64, f"Paket je moc krátký {len(pkt)}"
        tx_packet = bytes([0x00]) + bytes(pkt)
        self._dev.write(list(tx_packet))
        print(f"[TX] {bytes(pkt)[:8].hex(' ')} ...")

    # RX
    def receive_packet(self, size: int = 65) -> Packet | None:
        try:
            raw = self._dev.read(size)
            if not raw:
                return None
            b = Packet.parse(bytes(raw))
            print(f"[RX] {b[:8].hex(' ')} ...")
            return b
        except Exception:
            return None

    # Ping
    def ping(self, timeout: float = PING_TIMEOUT_S) -> bool:
        """Pošle PING a čeká na PONG. Vrátí True při úspěchu."""
        if not self.is_open:
            return False
        self.send_packet(make_ping())
        return self._wait_for_rsp(RSP_PONG, timeout) is not None

    # Konfigurace, pošle a čeká na ACK nebo ERR
    def send_config(self, cfg) -> tuple[bool, str]:
        if not self.is_open:
            return False, "Device not connected."
        self.send_packet(make_config(cfg))
        pkt = self._wait_for_rsps([RSP_ACK, RSP_ERR], CONFIG_TIMEOUT_S)
        if pkt is None:
            return False, "Device did not respond to configuration (timeout)."
        if pkt.is_err:
            return False, pkt.error_message
        return True, ""

    # Čtení dat (DATA_FRAME)
    def read_frame(self) -> Packet | None:
        if not self.is_open:
            return None
        data = self._read_nonblocking()
        if data is None:
            return None
        return Packet.parse(data)


    def _write(self, data: bytes):
        self._dev.write(list(data))
        print(f"[HID TX] {data[:8].hex(' ')} ...")
        print(f"[TX D] {data[1:8].hex(' ')} ...")

    def _read_nonblocking(self, size: int = 64) -> bytes | None:
        try:
            data = self._dev.read(size)
            if not data:
                return None
            b = bytes(data)
            print(f"[RX] {b[:8].hex(' ')} ...")
            return b
        except Exception:
            return None

    def _wait_for_rsp(self, rsp: int, timeout: float) -> Packet | None:
        return self._wait_for_rsps([rsp], timeout)

    def _wait_for_rsps(self, rsps: list[int], timeout: float) -> Packet | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            data = self._read_nonblocking()
            if data:
                pkt = Packet.parse(data)
                if pkt:
                    print(f"[WAIT] got rsp=0x{pkt.rsp:02X}, expecting {[hex(r) for r in rsps]}")
                if pkt and pkt.rsp in rsps:
                    return pkt
            time.sleep(0.005)
        print(f"[WAIT] timeout, expecting {[hex(r) for r in rsps]}")
        return None

    def send_la_run(self) -> None:
        self.send_packet(make_la_run())

    def send_la_stop(self) -> None:
        self.send_packet(make_la_stop())

    # žádost o vzorek + čeká na odpověď
    def send_dl_sample_request(self) -> tuple[bool, list[int]]:
        self.send_packet(make_dl_sample_request())
        pkt = self._wait_for_rsps([RSP_DL_DATA], 3.0)
        if pkt is None:
            return False, []
        return True, pkt.dl_channels

# HidWorker — connect + ping v QThread
class HidWorker(QThread):
    connected = pyqtSignal(object)
    error     = pyqtSignal(str)

    def __init__(self, vid: int | None = None, pid: int | None = None, parent=None):
        super().__init__(parent)
        self._vid = vid
        self._pid = pid

    def run(self):
        dev = HidDevice()

        if not dev.connect(self._vid, self._pid):
            self.error.emit(
                "Device not found.\n\n"
                "Check if it is connected via USB."
            )
            return

        if not dev.ping():
            dev.close()
            self.error.emit("Device not responding.")
            return

        self.connected.emit(dev)

# ConfigWorker — odeslání konfigurace v QThread
class ConfigWorker(QThread):

    success = pyqtSignal()
    error   = pyqtSignal(str)

    def __init__(self, device: HidDevice, cfg, parent=None):
        super().__init__(parent)
        self._device = device
        self._cfg = cfg

    def run(self):
        ok, msg = self._device.send_config(self._cfg)
        if ok:
            self.success.emit()
        else:
            self.error.emit(msg)

class DlSampleWorker(QThread):

    sample_received = pyqtSignal(list)
    error = pyqtSignal()

    def __init__(self, device: HidDevice, parent=None):
        super().__init__(parent)
        self._device = device

    def run(self):
        ok, channels = self._device.send_dl_sample_request()
        if ok:
            self.sample_received.emit(channels)
        else:
            self.error.emit()

# příjem LA paketů, odesílání ACK, ukládání do CSV
class LaDataWorker(QThread):

    os.makedirs(DATA_DIR, exist_ok=True)
    packet_received = pyqtSignal(object)  # Packet
    finished_capture = pyqtSignal()

    def __init__(self, device: HidDevice, parent=None):
        super().__init__(parent)
        self._device = device
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        with open(os.path.join(DATA_DIR, "la_log.csv"), "w") as f:
            f.write("CH0,CH1,CH2,CH3,CH4,CH5,CH6,CH7\n")

            while self._running:
                data = self._device._read_nonblocking()
                if data:
                    pkt = Packet.parse(data)
                    if pkt and pkt.is_la_end:
                        print(f"[LA] konec přenosu, celkem vzorků: {pkt.la_total_samples}")
                        self._running = False
                    elif pkt and pkt.is_la_data:
                        self._device.send_packet(make_ack())
                        self.packet_received.emit(pkt)
                        for byte in pkt.la_payload:
                            bits = [(byte >> i) & 1 for i in range(8)]
                            f.write(",".join(map(str, bits)) + "\n")
                else:
                    time.sleep(0.001)

        self.finished_capture.emit()