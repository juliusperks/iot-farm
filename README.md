# iot-farm

A simulated IoT agricultural monitoring system for a sheep farm in Gippsland, Victoria. Built as a security engineering project to demonstrate iterative hardening of MQTT communications.

## What it does

Six Docker containers simulate a farm network:

- **broker** — Mosquitto MQTT broker with authentication, ACLs, and TLS 1.3
- **device** — Paddock sensor publishing temperature and battery telemetry every 5 seconds
- **subscriber** — Receives telemetry and stores it in a SQLite database
- **monitor** — Watches for devices going offline and displays live sensor readings
- **weather** — Pulls real Gippsland weather data from Open-Meteo and publishes it every 60 seconds
- **gate** — Paddock gate actuator that opens below 5°C frost threshold, follows time-based rules, and accepts manual commands

All inter-container communication is encrypted with TLS 1.3 on port 8883. Messages are signed with HMAC-SHA256. Incoming weather messages are validated against a 30-second timestamp window to prevent replay attacks.

## Requirements

- Docker and Docker Compose
- Python 3.8+ (for running tests locally)
- `paho-mqtt` and `requests` (see `requirements.txt`)

## Running the system

```bash
# Build all containers
docker-compose build

# Start the system
docker-compose up -d

# View logs
docker-compose logs --tail=20

# Stop the system
docker-compose down
```

To send a manual command to the gate, first extract the CA certificate from the broker container:

```bash
docker cp iot-farm-broker-1:/tmp/ca.crt /tmp/ca.crt
```

Then publish a command:

```bash
mosquitto_pub -h localhost -p 8883 --cafile /tmp/ca.crt --insecure \
  -u iot-monitor -P farm123 \
  -t "farm/paddock-gate-01/commands" \
  -m '{"command": "OPEN"}'
```

Valid commands are `OPEN`, `CLOSE`, and `AUTO`. AUTO returns the gate to automatic temperature and time-based control.

## Running the tests

Install dependencies:

```bash
pip install paho-mqtt requests pytest
```

Run the full test suite:

```bash
pytest tests/ -v
```

Run tests for a specific component:

```bash
pytest tests/test_gate.py -v
pytest tests/test_weather_station.py -v
pytest tests/test_subscriber.py -v
pytest tests/test_monitor.py -v
pytest tests/test_telemetry.py -v
```

## Notes

- TLS certificates are generated at build time inside the broker container and are never written to the repository
- The shared HMAC secret (`farmkey123`) is hardcoded for demonstration purposes — in production this would be managed securely
- The timestamp validation window assumes synchronised clocks. All Docker containers share the host clock so this holds in this environment. Physical hardware deployments would require NTP
