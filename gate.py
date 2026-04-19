import json
import os
import time
from datetime import datetime, timezone
from enum import Enum
import hmac
import hashlib
import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))
DEVICE_ID = os.getenv("DEVICE_ID", "paddock-gate-01")
TELEMETRY_TOPIC = f"farm/{DEVICE_ID}/telemetry"
COMMAND_TOPIC = f"farm/{DEVICE_ID}/commands"
SHARED_SECRET = "farmkey123"  # In production, use a secure method to store secrets
interval = 10  # seconds

class GateState(Enum):
    OPEN = "open"
    CLOSED = "closed"

class PaddockGate:
    def __init__(self, device_id, frost_threshold: float = 5.0, open_hour: int = 6, close_hour: int = 20):
        self.device_id = device_id
        self.frost_threshold = frost_threshold
        self.open_hour = open_hour
        self.close_hour = close_hour
        self.state = GateState.CLOSED
        self.temperature = None
        self._command_override = None
    
    def update_weather(self, termperature: float):
        self.temperature = termperature
        if self._command_override is None:
            if self.temperature < self.frost_threshold:
                self.state = GateState.OPEN
            else:
                self.state = GateState.CLOSED
    
    def _apply_time_rules(self):
        hour = datetime.now(timezone.utc).hour
        if seld.open_hour <= hour < self.close_hour:
            self.state = GateState.OPEN
        else:
            self.state = GateState.CLOSED
        
    def handle_command(self, command: str):
        if command == "OPEN":
            self._command_override = GateState.OPEN
            self.state = GateState.OPEN
        elif command == "CLOSE":
            self._command_override = GateState.CLOSED
            self.state = GateState.CLOSED
        elif command == "AUTO":
            self._command_override = None
            self._apply_time_rules()

    def get_telemetry(self) -> dict:
        payload = {
            "device_id": self.device_id,
            "state": self.state.value,
            "temperature": self.temperature,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        payload["hash"] = hmac.new(
            SHARED_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return payload
    
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{DEVICE_ID}] Connected")
        client.subscribe(COMMAND_TOPIC, qos=1)
        print(f"[{DEVICE_ID}] Subscribed to {COMMAND_TOPIC}")
    else:
        print(f"[{DEVICE_ID}] Failed rc={rc}")

def on_message(client, userdata, msg):
    gate = userdata
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("command", "").upper()
        print(f"[{DEVICE_ID}] Received command: {command}")
        gate.handle_command(command)
    except Exception as e:
        print(f"[{DEVICE_ID}] Bad command message: {e}")

if __name__ == "__main__":
    gate = PaddockGate(device_id=DEVICE_ID)
    client = mqtt.Client(client_id=DEVICE_ID, userdata=gate)
    client.username_pw_set("paddock-gate-01", "farm123")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    
    client.loop_start()

    print(f"[{DEVICE_ID}] Running...")
    try:
        while True:
            payload = gate.get_telemetry()
            client.publish(TELEMETRY_TOPIC, json.dumps(payload), qos=1)
            print(f"[{DEVICE_ID}] {payload}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"[{DEVICE_ID}] Shutting down")
    finally:
        client.loop_stop()
        client.disconnect()