import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from monitor import DeviceMonitor, DeviceStatus

class TestDeviceMonitor:

    @pytest.fixture
    def monitor(self):
        return DeviceMonitor(offline_threshold_seconds=15)

    def _ts(self, seconds_ago):
        return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).isoformat()

    def test_online_when_recently_seen(self, monitor):
        assert monitor.evaluate({"s1": self._ts(5)})["s1"] == DeviceStatus.ONLINE

    def test_offline_when_not_heard_from(self, monitor):
        assert monitor.evaluate({"s1": self._ts(30)})["s1"] == DeviceStatus.OFFLINE

    def test_offline_at_threshold(self, monitor):
        assert monitor.evaluate({"s1": self._ts(15)})["s1"] == DeviceStatus.OFFLINE

    def test_multiple_devices_independent(self, monitor):
        result = monitor.evaluate({"s1": self._ts(5), "s2": self._ts(60)})
        assert result["s1"] == DeviceStatus.ONLINE
        assert result["s2"] == DeviceStatus.OFFLINE

    def test_empty_returns_empty(self, monitor):
        assert monitor.evaluate({}) == {}

    def test_alert_callback_fires_for_offline_only(self, monitor):
        alert = MagicMock()
        monitor.evaluate({"s1": self._ts(5), "s2": self._ts(60)}, on_offline=alert)
        alert.assert_called_once_with("s2")