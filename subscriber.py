import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import paho.mqtt.client as mqtt
import hashlib
import hmac as hmac_lib

BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))
SUBSCRIBE_TOPIC = "farm/+/telemetry"
DB_PATH         = "telemetry.db"
SHARED_SECRET = "farmkey123"  # Must match the device's secret for hash validation

def parse_payload(raw: bytes) -> Optional[dict]:
    if not raw:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if "device_id" not in payload:
        return None
    try:
        payload["temperature"] = float(payload["temperature"])
        payload["battery"]     = float(payload["battery"])
    except (KeyError, TypeError, ValueError):
        return None
    return payload

def verify_payload(payload: dict) -> bool:
    received_hash = payload.get("hash")
    if not received_hash:
        return False
    check = {k: v for k, v in payload.items() if k != "hash"}
    payload_bytes = json.dumps(check, sort_keys=True).encode()
    expected = hmac_lib.new(
        SHARED_SECRET.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac_lib.compare_digest(received_hash, expected)

class MessageStore:
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   TEXT NOT NULL,
                received_at TEXT NOT NULL,
                temperature REAL,
                battery     REAL,
                raw         TEXT
            )
        """)
        self.conn.commit()

    def insert(self, payload: dict):
        self.conn.execute("""
            INSERT INTO telemetry (device_id, received_at, temperature, battery, raw)
            VALUES (?, ?, ?, ?, ?)
        """, (payload["device_id"], datetime.now(timezone.utc).isoformat(),
              payload.get("temperature"), payload.get("battery"), json.dumps(payload)))
        self.conn.commit()

    def get_all(self) -> list:
        return [dict(r) for r in self.conn.execute("SELECT * FROM telemetry ORDER BY id")]

    def get_last_seen(self) -> dict:
        cursor = self.conn.execute("""
            SELECT device_id, MAX(received_at) as last_seen
            FROM telemetry GROUP BY device_id
        """)
        return {r["device_id"]: r["last_seen"] for r in cursor}

    def close(self):
        self.conn.close()

_store = MessageStore()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(SUBSCRIBE_TOPIC, qos=1)
        print(f"[subscriber] Subscribed to {SUBSCRIBE_TOPIC}")

def on_message(client, userdata, msg):
    payload = parse_payload(msg.payload)
    if payload is None:
        print(f"[subscriber] Rejected bad message")
        return
    if not verify_payload(payload):
        print(f"[subscriber] Rejected message — hash verification failed")
        return
    _store.insert(payload)
    print(f"[subscriber] Stored {payload['device_id']}")

if __name__ == "__main__":
    client = mqtt.Client(client_id="cloud-subscriber")
    client.username_pw_set("cloud-subscriber", "farm123")
    client.tls_set(ca_certs="/app/ca.crt")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_forever()