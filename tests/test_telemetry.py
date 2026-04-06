import json
import pytest
from device import get_telemetry, DEVICE_ID

class TestTelemetryPayload:

    def test_payload_is_valid_json(self):
        payload = get_telemetry()
        assert isinstance(json.dumps(payload), str)

    def test_payload_has_required_fields(self):
        payload = get_telemetry()
        assert {"device_id", "timestamp", "temperature", "battery"}.issubset(payload.keys())

    def test_device_id_is_string(self):
        assert isinstance(get_telemetry()["device_id"], str)

    def test_temperature_in_range(self):
        temp = get_telemetry()["temperature"]
        assert isinstance(temp, float)
        assert 0.0 <= temp <= 60.0

    def test_battery_in_range(self):
        battery = get_telemetry()["battery"]
        assert isinstance(battery, float)
        assert 0.0 <= battery <= 100.0

    def test_timestamp_has_timezone(self):
        from datetime import datetime
        ts = datetime.fromisoformat(get_telemetry()["timestamp"])
        assert ts.tzinfo is not None

    def test_battery_drains_over_time(self):
        first = get_telemetry()["battery"]
        for _ in range(200):
            get_telemetry()
        assert get_telemetry()["battery"] < first
    
    def test_payload_contains_hash(self):
        payload = get_telemetry()
        assert "hash" in payload
        hash_val = payload["hash"]
        assert isinstance(payload["hash"], str)
        assert len(payload["hash"]) == 64  # SHA-256 hash length

    def test_hash_is_valid_sha256_of_payload(self):
        import hashlib
        payload = get_telemetry()
        hash_received = payload.pop("hash")
        recomputed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        assert hash_received == recomputed