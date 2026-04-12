import json
import random
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import hashlib
import hmac
import os

BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))
DEVICE_ID = os.getenv("DEVICE_ID", "paddock-sensor-01")
TOPIC       = f"farm/{DEVICE_ID}/telemetry"
INTERVAL    = 5

_battery_level = 100.0

SHARED_SECRET = "farmkey123"  # In a real scenario, this should be securely stored and not hardcoded

def get_telemetry() -> dict:
    global _battery_level
    _battery_level = max(0.0, _battery_level - random.uniform(0.01, 0.05))
    payload = {
        "device_id":   DEVICE_ID,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "temperature": round(random.uniform(18.0, 35.0), 2),
        "battery":     round(_battery_level, 2),
    }

    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    payload["hash"] = hmac.new(
        SHARED_SECRET.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return payload


def on_connect(client, userdata, flags, rc):
    print(f"[{DEVICE_ID}] Connected" if rc == 0 else f"[{DEVICE_ID}] Failed rc={rc}")

if __name__ == "__main__":
    client = mqtt.Client(client_id=DEVICE_ID)
    client.username_pw_set("paddock-sensor-01", "farm123")
    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    try:
        while True:
            payload = get_telemetry()
            client.publish(TOPIC, json.dumps(payload), qos=1)
            print(f"[{DEVICE_ID}] {payload}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()