"""КРИТИЧНЫЙ СЦЕНАРИЙ: подключение к сервису и получение полного набора корректных сигналов.
"""
from __future__ import annotations

import math

import pytest

from config.settings import settings
from framework.client import SignalServiceClient, SignalServiceError
from framework.models import ALLOWED_QUALITIES


@pytest.mark.critical
@pytest.mark.smoke
def test_connect_receives_full_valid_signal_set(client: SignalServiceClient):
    # соединение уже установлено фикстурой, ожидание первых значений
    signals = client.receive_snapshot()

    # 1. Получено ровно ожидаемое число сигналов.
    assert len(signals) == settings.expected_signal_count, (
        f"Ожидалось {settings.expected_signal_count} сигналов, получено {len(signals)}"
    )

    # 2. ID уникальны (в таблице не будет дублей и потерянных строк).
    ids = [s.id for s in signals]
    assert len(set(ids)) == len(ids), f"Дубликаты ID: {ids}"

    for s in signals:
        # 3. Имя не пустое.
        assert s.name.strip(), f"Сигнал {s.id}: пустое имя"
        # 4. Значение — конечное число (не NaN / Inf)
        assert math.isfinite(s.value), f"Сигнал {s.id}: недопустимое значение {s.value}"
        # 5. Качество — одно из допустимых
        assert s.quality in ALLOWED_QUALITIES, f"Сигнал {s.id}: неизвестное качество {s.quality!r}"
        # 6. Метка времени актуальна 
        age = s.age_seconds()
        assert -2 <= age <= settings.max_timestamp_age_sec, f"Сигнал {s.id}: возраст метки {age:.1f} c"


@pytest.mark.critical
def test_signal_values_change_between_updates(client: SignalServiceClient):
    """Значения корректные, после ручного обновления хотя бы один сигнал изменился."""
    first = {s.id: s.value for s in client.receive_snapshot()}

    client.request_refresh()
    second = {s.id: s.value for s in client.receive_snapshot()}

    assert first.keys() == second.keys(), "Набор ID изменился между обновлениями"
    assert any(first[i] != second[i] for i in first), "Значения не меняются — данные «замёрзли»"


@pytest.mark.smoke
def test_connect_to_unavailable_port_fails_fast():
    """Негативная проверка клиента: недоступный порт даёт понятную ошибку, а не зависание."""
    unavailable = SignalServiceClient(settings.host, 1, connect_timeout=1)
    with pytest.raises(SignalServiceError):
        unavailable.connect()
