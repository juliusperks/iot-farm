import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from gate import PaddockGate, GateState

class TestGateState:
    @pytest.fixture
    def gate(self):
        return PaddockGate(
            device_id="paddock-gate-01",
            frost_threshold=5.0,
            open_hour=6,
            close_hour=20
        )
    
    def test_gate_starts_closed(self, gate):
        assert gate.state == GateState.CLOSED
    
    def test_gate_opens_on_frost(self, gate):
        gate.update_weather(termperature=3.0)
        assert gate.state == GateState.OPEN
    
    def test_gate_stays_closed_when_above_threshold(self, gate):
        gate.update_weather(termperature=10.0)
        assert gate.state == GateState.CLOSED

    def test_gate_opens_on_command(self, gate):
        gate.handle_command("OPEN")
        assert gate.state == GateState.OPEN
    
    def test_gate_closes_on_command(self, gate):
        gate.handle_command("OPEN")
        gate.handle_command("CLOSE")
        assert gate.state == GateState.CLOSED

    def test_invalid_command_ignored(self, gate):
        gate.handle_command("EXPLODE")
        assert gate.state == GateState.CLOSED

    def test_gate_publishes_state(self, gate):
        payload = gate.get_telemetry()
        assert "device_id" in payload
        assert "state" in payload
        assert "temperature" in payload
        assert "timestamp" in payload

    def test_telemetry_state_is_string(self, gate):
        payload = gate.get_telemetry()
        assert payload["state"] in ["open", "closed"]