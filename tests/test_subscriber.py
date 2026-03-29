import json
import pytest
from subscriber import MessageStore, parse_payload

class TestParsePayload:

    def test_valid_json_returns_dict(self):
        raw = b'{"device_id":"sensor-01","timestamp":"2026-01-01T00:00:00+00:00","temperature":22.5,"battery":95.0}'
        result = parse_payload(raw)
        assert isinstance(result, dict)
        assert result["device_id"] == "sensor-01"

    def test_invalid_json_returns_none(self):
        assert parse_payload(b"not json {{{") is None

    def test_empty_returns_none(self):
        assert parse_payload(b"") is None

    def test_missing_device_id_returns_none(self):
        raw = json.dumps({"temperature": 22.5, "battery": 90.0}).encode()
        assert parse_payload(raw) is None

    def test_non_numeric_temperature_returns_none(self):
        raw = json.dumps({"device_id": "s1", "timestamp": "2026-01-01T00:00:00+00:00",
                          "temperature": "hot", "battery": 90.0}).encode()
        assert parse_payload(raw) is None

class TestMessageStore:

    @pytest.fixture
    def store(self, tmp_path):
        from subscriber import MessageStore
        s = MessageStore(str(tmp_path / "test.db"))
        yield s
        s.close()

    def test_store_initialises(self, store):
        assert store is not None

    def test_insert_and_retrieve(self, store):
        store.insert({"device_id": "s1", "timestamp": "2026-01-01T00:00:00+00:00",
                      "temperature": 22.5, "battery": 95.0})
        rows = store.get_all()
        assert len(rows) == 1
        assert rows[0]["device_id"] == "s1"

    def test_multiple_devices(self, store):
        for did in ["s1", "s2", "s3"]:
            store.insert({"device_id": did, "timestamp": "2026-01-01T00:00:00+00:00",
                          "temperature": 20.0, "battery": 80.0})
        assert len(store.get_all()) == 3

    def test_get_last_seen(self, store):
        store.insert({"device_id": "s1", "timestamp": "2026-01-01T00:00:00+00:00",
                      "temperature": 20.0, "battery": 80.0})
        store.insert({"device_id": "s1", "timestamp": "2026-01-01T00:01:00+00:00",
                      "temperature": 21.0, "battery": 79.0})
        last = store.get_last_seen()
        assert "s1" in last