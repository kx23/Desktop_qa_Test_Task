"""TCP-клиент сервиса сигналов

Симулирует поведение приложения при нажатии «Подключиться» / «Обновить».
"""
from __future__ import annotations

import json
import logging
import socket

from framework.models import Signal

log = logging.getLogger(__name__)


class SignalServiceError(Exception):
    """Ошибка взаимодействия с сервисом сигналов."""


class SignalServiceClient:
    def __init__(self, host: str, port: int, connect_timeout: float = 5.0, read_timeout: float = 5.0):
        self._host, self._port = host, port
        self._connect_timeout, self._read_timeout = connect_timeout, read_timeout
        self._sock: socket.socket | None = None
        self._reader = None

    # управление соединением 
    def connect(self) -> None:
        log.info("Подключение к %s:%s", self._host, self._port)
        try:
            self._sock = socket.create_connection((self._host, self._port), timeout=self._connect_timeout)
        except OSError as exc:
            raise SignalServiceError(f"Не удалось подключиться к {self._host}:{self._port}: {exc}") from exc
        self._sock.settimeout(self._read_timeout)
        self._reader = self._sock.makefile("r", encoding="utf-8", newline="\n")

    def close(self) -> None:
        for closable in (self._reader, self._sock):
            try:
                if closable:
                    closable.close()
            except OSError:
                pass
        self._sock = self._reader = None

    def __enter__(self) -> "SignalServiceClient":
        self.connect()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # операции протокола 
    def request_refresh(self) -> None:
        self._send("REFRESH")

    def receive_snapshot(self) -> list[Signal]:
        """ читает одно сообщение и возвращает список сигналов."""
        if self._reader is None:
            raise SignalServiceError("Соединение не установлено")
        try:
            line = self._reader.readline()
        except (socket.timeout, TimeoutError) as exc:
            raise SignalServiceError(f"Сервис не прислал данные за {self._read_timeout} c") from exc
        if not line:
            raise SignalServiceError("Сервис закрыл соединение")
        log.debug("RX: %s", line.strip())
        try:
            payload = json.loads(line)
            return [Signal.from_dict(item) for item in payload["signals"]]
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise SignalServiceError(f"Некорректное сообщение сервиса: {line!r} ({exc})") from exc

    def _send(self, command: str) -> None:
        if self._sock is None:
            raise SignalServiceError("Соединение не установлено")
        self._sock.sendall(f"{command}\n".encode("utf-8"))
