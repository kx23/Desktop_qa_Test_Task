"""Модель сигнала"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Допустимые значения качества сигнала.
ALLOWED_QUALITIES = frozenset({"GOOD", "BAD", "UNCERTAIN"})


@dataclass(frozen=True)
class Signal:
    id: int
    name: str
    value: float
    quality: str
    timestamp: datetime

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Signal":
        missing = {"id", "name", "value", "quality", "timestamp"} - raw.keys()
        if missing:
            raise ValueError(f"В сигнале отсутствуют поля: {sorted(missing)}; raw={raw}")
        ts = datetime.fromisoformat(str(raw["timestamp"]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return cls(
            id=int(raw["id"]),
            name=str(raw["name"]),
            value=float(raw["value"]),
            quality=str(raw["quality"]),
            timestamp=ts,
        )

    def is_value_finite(self) -> bool:
        return math.isfinite(self.value)

    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds()
