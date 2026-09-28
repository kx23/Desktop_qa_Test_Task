"""Симулятор сервиса

Запуск отдельным процессом:  python -m simulator.signal_simulator --port 2001
Нужен, чтобы тесты были самодостаточными. При работе с настоящим симулятором
необходимо задать переменной USE_EXTERNAL_SERVICE=1. Создан с помощью ии.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import socketserver
import threading
import time
from datetime import datetime, timezone

SIGNAL_COUNT = 10
PUSH_INTERVAL_SEC = 1.0


def build_snapshot() -> bytes:
    now = time.time()
    signals = []
    for i in range(1, SIGNAL_COUNT + 1):
        # Нечётные — синусоида с разной фазой, чётные — случайные значения.
        value = 50 + 40 * math.sin(now / 3 + i) if i % 2 else random.uniform(0, 100)
        signals.append({
            "id": i,
            "name": f"SIGNAL_{i:02d}",
            "value": round(value, 3),
            "quality": "GOOD",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return (json.dumps({"type": "snapshot", "signals": signals}) + "\n").encode("utf-8")


class Handler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        lock, stop = threading.Lock(), threading.Event()

        def send() -> None:
            with lock:
                self.request.sendall(build_snapshot())

        def pusher() -> None:
            while not stop.wait(PUSH_INTERVAL_SEC):
                try:
                    send()
                except OSError:
                    return

        try:
            send() 
            threading.Thread(target=pusher, daemon=True).start()
            reader = self.request.makefile("r", encoding="utf-8")
            for line in reader:
                if line.strip() == "REFRESH":
                    send()
        except OSError:
            pass
        finally:
            stop.set()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2001)
    args = parser.parse_args()
    with Server((args.host, args.port), Handler) as server:
        print(f"Simulator listening on {args.host}:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
