import json
import os
import time
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional
import requests
import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", 8883))
DEVICE_ID = os.getenv("DEVICE_ID", "gippsland-weather-01")
TELEMETRY_TOPIC = f"farm/{DEVICE_ID}/telemetry"
SHARED_SECRET = "farmkey123"
INTERVAL = 60

# Gippsland, Victoria — approximate coordinates for the region
LATITUDE = -38.1
LONGITUDE = 146.8

OPEN_METEO_URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LATITUDE}&longitude={LONGITUDE}"
    f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
)


def parse_weather_response(response: dict) -> Optional[dict]:
    if not response:
        return None
    try:
        current = response["current"]
        return {
            "temperature": float(current["temperature_2m"]),
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
        }
    except (KeyError, TypeError, ValueError):
        return None


class GippslandWeatherStation:
    def __init__(self, device_id: str = DEVICE_ID):
        self.device_id       = device_id
        self.current_weather = None

    def fetch(self):
        try:
            response = requests.get(OPEN_METEO_URL, timeout=10)
            data = response.json()
            parsed = parse_weather_response(data)
            if parsed:
                self.current_weather = parsed
                print(f"[{self.device_id}] Weather updated: {parsed}")
            else:
                print(f"[{self.device_id}] Failed to parse weather response")
        except Exception as e:
            print(f"[{self.device_id}] Fetch error: {e}")

    def get_telemetry(self) -> Optional[dict]:
        if not self.current_weather:
            return None
        payload = {
            "device_id": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.current_weather,
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
        print(f"[{DEVICE_ID}] Connected to broker")
    else:
        print(f"[{DEVICE_ID}] Failed rc={rc}")


if __name__ == "__main__":
    station = GippslandWeatherStation(device_id=DEVICE_ID)
    client = mqtt.Client(client_id=DEVICE_ID)
    client.username_pw_set("gippsland-weather-01", "farm123")
    client.tls_set(ca_certs="/app/ca.crt")
    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    print(f"[{DEVICE_ID}] Starting weather station for Gippsland, VIC")
    try:
        while True:
            station.fetch()
            payload = station.get_telemetry()
            if payload:
                client.publish(TELEMETRY_TOPIC, json.dumps(payload), qos=1)
                print(f"[{DEVICE_ID}] Published: {payload}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()