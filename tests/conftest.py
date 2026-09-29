"""Фикстура"""
from __future__ import annotations

import pytest

from config.settings import settings
from framework.client import SignalServiceClient
from framework.simulator_process import SimulatorProcess


@pytest.fixture(scope="session", autouse=True)
def signal_service():
    """Поднимает симулятор один раз на сессию, если не задан внешний сервис."""
    if settings.use_external_service:
        yield
        return
    simulator = SimulatorProcess(settings.host, settings.port)
    simulator.start()
    yield
    simulator.stop()


@pytest.fixture
def client(signal_service):
    """Новое соединение на каждый тест - атомарность"""
    with SignalServiceClient(
        settings.host, settings.port, settings.connect_timeout, settings.read_timeout
    ) as connected_client:
        yield connected_client
