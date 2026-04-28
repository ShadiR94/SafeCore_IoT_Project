# SafeCore_Project/emulators/door_sensor.py

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from models.mqtt_client import MQTTClient
from mqtt_config import (
    CLIENT_ID_DOOR_SENSOR,
    DEVICE_ID_DOOR,
    ROOM_ZONE,
    TOPIC_DOOR_STATUS,
)


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    mqtt_client = MQTTClient(CLIENT_ID_DOOR_SENSOR)
    mqtt_client.connect()

    current_state = "closed"

    print("[DOOR SENSOR] SafeCore Door Sensor started")
    print("[DOOR SENSOR] Commands:")
    print("  o = open")
    print("  c = close")
    print("  t / Enter = toggle")
    print("  q = quit")

    try:
        while True:
            command = input("Command: ").strip().lower()

            if command == "q":
                break
            elif command == "o":
                current_state = "open"
            elif command == "c":
                current_state = "closed"
            else:
                current_state = "open" if current_state == "closed" else "closed"

            payload = {
                "device_id": DEVICE_ID_DOOR,
                "type": "door_sensor",
                "zone": ROOM_ZONE,
                "door_state": current_state,
                "ts": now_text(),
            }

            payload_text = json.dumps(payload)

            print(f"[DOOR SENSOR] Sending: {payload_text}")
            mqtt_client.publish(TOPIC_DOOR_STATUS, payload_text, qos=1)

    except KeyboardInterrupt:
        print("[DOOR SENSOR] Stopping...")

    mqtt_client.disconnect()


if __name__ == "__main__":
    main()