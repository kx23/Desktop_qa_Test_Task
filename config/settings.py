"""Файл конфигурации"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("SERVICE_HOST", "127.0.0.1")
    port: int = int(os.getenv("SERVICE_PORT", "2001"))
    # 1 - еслит тесты не запускают симулятор, а используют уже работающий сервис.
    use_external_service: bool = os.getenv("USE_EXTERNAL_SERVICE", "0") == "1"
    connect_timeout: float = float(os.getenv("CONNECT_TIMEOUT", "5"))
    read_timeout: float = float(os.getenv("READ_TIMEOUT", "5"))
    expected_signal_count: int = int(os.getenv("EXPECTED_SIGNAL_COUNT", "10"))
    # Максимально допустимый таймаут метки времени сигнала, секунд.
    max_timestamp_age_sec: float = float(os.getenv("MAX_TIMESTAMP_AGE_SEC", "10"))


settings = Settings()
