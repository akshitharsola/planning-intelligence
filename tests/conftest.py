import pytest

from src.monitoring import metrics


@pytest.fixture(autouse=True)
def _reset_metrics_counters():
    metrics._counters.clear()
    yield
    metrics._counters.clear()
