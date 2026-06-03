from __future__ import annotations
from dataclasses import dataclass

PACKET_SIZE = 64
START_BYTE  = 0xAA

# Módy konfigurace
MODE_PING   = 0xAA
MODE_LA     = 0x01
MODE_DL     = 0x02
MODE_REMOTE = 0x03

# Odpovědi zařízení
RSP_PONG = 0x02
RSP_ACK  = 0x06
RSP_ERR  = 0xFF
RSP_DL_DATA = 0x03

# -- Odchozí pakety ---
def make_ping() -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = START_BYTE
    pkt[1] = MODE_PING
    return bytes([0x00]) + bytes(pkt)


def make_config(cfg) -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = START_BYTE

    match cfg.device_mode:

        case "Logic Analyzer":

            pkt[1] = MODE_LA
            pkt[4] = cfg.sample_rate_khz & 0xFF
            pkt[6] = (cfg.sample_rate_khz >> 8) & 0xFF
            pkt[7] = (cfg.sample_rate_khz >> 16) & 0xFF
            pkt[8] = (cfg.sample_rate_khz >> 24) & 0xFF
            pkt[9] = 0 if cfg.la_voltage == "5V" else 1

        case "Data Logger":

            match cfg.logger_mode:

                case "Real-time Auto" | "Real-time Manual":

                    ch_mask = 0
                    for i, ch in enumerate(cfg.channels[:4]):
                        if ch.enabled:
                            ch_mask |= (1 << i)

                    pkt[1] = MODE_DL
                    pkt[4] = ch_mask

                case "Remote":
                    import datetime
                    epoch = datetime.datetime(2026, 1, 1, 0, 0, 0)
                    now = datetime.datetime.now()
                    unix_custom = int((now - epoch).total_seconds())

                    period = cfg.log_period_s
                    hours = cfg.log_duration_s
                    sample_count = (hours * 3600 // period) if period > 0 else 0
                    sample_count = min(sample_count, 0xFFFFFFFF)

                    ch_byte = 0
                    for i, ch in enumerate(cfg.channels[:4]):
                        if ch.enabled:
                            ch_byte |= (1 << i)

                    pkt[1] = MODE_REMOTE
                    pkt[4] = unix_custom & 0xFF
                    pkt[5] = (unix_custom >> 8) & 0xFF
                    pkt[6] = (unix_custom >> 16) & 0xFF
                    pkt[7] = (unix_custom >> 24) & 0xFF
                    pkt[8] = period & 0xFF
                    pkt[9] = (period >> 8) & 0xFF
                    pkt[10] = (period >> 16) & 0xFF
                    pkt[11] = (period >> 24) & 0xFF
                    pkt[12] = sample_count & 0xFF
                    pkt[13] = (sample_count >> 8) & 0xFF
                    pkt[14] = (sample_count >> 16) & 0xFF
                    pkt[15] = (sample_count >> 24) & 0xFF
                    pkt[16] = ch_byte
                    print(f"[config] {pkt[:16].hex(' ')}")
    return bytes(pkt)

def make_la_run() -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = START_BYTE
    pkt[1] = 0x01
    pkt[4] = 0xFF
    return bytes(pkt)


def make_la_stop() -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = START_BYTE
    pkt[1] = 0x01
    pkt[4] = 0x00
    return bytes(pkt)

def make_ack() -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = START_BYTE
    pkt[1] = RSP_ACK
    return bytes(pkt)

def make_dl_sample_request() -> bytes:
    pkt = bytearray(PACKET_SIZE)
    pkt[0] = START_BYTE
    pkt[1] = 0x03
    pkt[2] = 0x00
    pkt[3] = 0x00
    pkt[4] = 0xFF
    return bytes(pkt)

RSP_DL_DATA = 0x03

# --- Parsování příchozích paketů ---

# [0..3] header
# [0]  0xAA  start byte
# [1]  typ odpovědi  (RSP_PONG=0x02, RSP_ACK=0x06, RSP_ERR=0xFF)
# [2]  aktuální čas
# [3]  rezervováno
# [4..63] payload

@dataclass
class Packet:
    raw: bytes
    rsp: int
    header: bytes
    payload: bytes

    @classmethod
    def parse(cls, data: bytes) -> "Packet | None":
        if data[0] == 0x00:
            data = data[1:]
        if len(data) < PACKET_SIZE:
            print(f"paket je příliš krátký {len(data)}")
            return None
        raw = bytes(data[:PACKET_SIZE])
        header = raw[0:4]
        rsp = raw[1]
        payload = raw[4:]
        #print(f"[RX D] {raw[:10].hex(' ')} ...")
        return cls(raw=raw, rsp=rsp, header=header, payload=payload)

    @property
    def is_pong(self) -> bool:
        return self.raw[1] == RSP_PONG

    @property
    def is_ack(self) -> bool:
        return self.rsp == RSP_ACK

    @property
    def is_err(self) -> bool:
        return self.rsp == RSP_ERR

    @property
    def error_message(self) -> str:
        try:
            return self.payload.decode("ascii").strip("\x00") or "Unknown device error"
        except Exception:
            return "Unknown device error"

    @property
    def is_la_data(self) -> bool:
        return self.raw[0] == START_BYTE and self.raw[1] == MODE_LA

    @property
    def la_packet_number(self) -> int:
        # Číslo paketu
        return int.from_bytes(self.raw[2:8], byteorder='little')

    @property
    def la_payload(self) -> bytes:
        # Binární data
        return self.raw[8:64]

    @property
    def is_la_end(self) -> bool:
        return self.raw[0] == START_BYTE and self.raw[1] == START_BYTE

    @property
    def la_total_samples(self) -> int:
        # Celkový počet vzorků
        return int.from_bytes(self.raw[2:6], byteorder='little')

    @property
    def is_dl_data(self) -> bool:
        return self.raw[0] == START_BYTE and self.raw[1] == RSP_DL_DATA

    @property
    def dl_channels(self) -> list[int]:
        # CH0–CH3
        return [
            int.from_bytes(self.raw[4 + i * 2: 6 + i * 2], byteorder='little')
            for i in range(4)
        ]