import json
import os
import time


def create_message(seq: int, payload_size: int) -> bytes:
    payload = os.urandom(payload_size)
    header = json.dumps({
        "seq": seq,
        "ts": time.time(),
        "ps": payload_size,
    }).encode()
    hl = len(header)
    return hl.to_bytes(4, "big") + header + payload


def parse_message(data: bytes) -> tuple:
    hl = int.from_bytes(data[:4], "big")
    header = json.loads(data[4:4 + hl])
    seq = header["seq"]
    ts = header["ts"]
    ps = header["ps"]
    actual_ps = len(data) - (4 + hl)
    return seq, ts, ps, actual_ps
