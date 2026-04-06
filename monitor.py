import time
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional
from subscriber import MessageStore

class DeviceStatus(Enum):
    ONLINE  = "online"
    OFFLINE = "offline"

class DeviceMonitor:
    def __init__(self, offline_threshold_seconds: int = 15):
        self.threshold = offline_threshold_seconds

    def evaluate(self, last_seen: dict, on_offline: Optional[Callable] = None) -> dict:
        now      = datetime.now(timezone.utc)
        statuses = {}
        for device_id, last_ts in last_seen.items():
            age = (now - datetime.fromisoformat(last_ts)).total_seconds()
            if age >= self.threshold:
                statuses[device_id] = DeviceStatus.OFFLINE
                if on_offline:
                    on_offline(device_id)
            else:
                statuses[device_id] = DeviceStatus.ONLINE
        return statuses

def format_reading(device_id: str, store: MessageStore) -> str:
    rows = store.conn.execute("""
        SELECT temperature, battery, received_at FROM telemetry
        WHERE device_id = ?
        ORDER BY id DESC LIMIT 1
    """, (device_id,)).fetchone()

    if not rows:
        return f"{device_id} | no data"

    temp    = rows["temperature"]
    battery = rows["battery"]

    temp_warn    = " [WARN: temp out of range]" if temp is not None and (temp > 60 or temp < 0) else ""
    battery_warn = " [WARN: battery low]" if battery is not None and battery < 10 else ""

    return (f"{device_id} | "
            f"temp: {temp}°C{temp_warn}| "
            f"battery: {battery}%{battery_warn}")

if __name__ == "__main__":
    store   = MessageStore()
    monitor = DeviceMonitor(offline_threshold_seconds=15)
    print("[monitor] Running...")
    try:
        while True:
            last_seen = store.get_last_seen()
            statuses  = monitor.evaluate(last_seen, on_offline=lambda d: print(f"[ALERT] {d} is OFFLINE"))
            for device_id, status in statuses.items():
                reading = format_reading(device_id, store)
                print(f"[{status.value.upper():7}] {reading}")
            print("---")
            time.sleep(5)
    except KeyboardInterrupt:
        print("[monitor] Stopped.")