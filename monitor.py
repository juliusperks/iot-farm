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

if __name__ == "__main__":
    store   = MessageStore()
    monitor = DeviceMonitor(offline_threshold_seconds=15)
    print("[monitor] Running...")
    try:
        while True:
            last_seen = store.get_last_seen()
            statuses  = monitor.evaluate(last_seen, on_offline=lambda d: print(f"[ALERT] {d} is OFFLINE"))
            for did, status in statuses.items():
                print(f"[{status.value.upper()}] {did}")
            print("---")
            time.sleep(5)
    except KeyboardInterrupt:
        print("[monitor] Stopped.")