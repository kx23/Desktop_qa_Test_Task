"""Управление жизненным циклом симулятора как отдельного процесса."""
from __future__ import annotations

import logging
import socket
import subprocess
import sys
import time
from pathlib import Path

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent


class SimulatorProcess:
    def __init__(self, host: str, port: int, startup_timeout: float = 10.0):
        self._host, self._port, self._startup_timeout = host, port, startup_timeout
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        log.info("Запуск симулятора на %s:%s", self._host, self._port)
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "simulator.signal_simulator", "--host", self._host, "--port", str(self._port)],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self._wait_until_listening()

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        log.info("Симулятор остановлен")

    def _wait_until_listening(self) -> None:
        """Ждём готовности порта"""
        deadline = time.monotonic() + self._startup_timeout
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                out = self._proc.stdout.read().decode(errors="replace")
                raise RuntimeError(f"Симулятор завершился при старте (порт занят?):\n{out}")
            try:
                with socket.create_connection((self._host, self._port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError(f"Симулятор не начал слушать порт {self._port} за {self._startup_timeout} c")
