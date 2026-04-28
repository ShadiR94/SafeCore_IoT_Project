# SafeCore_Project/emulators/smart_button.py

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from models.mqtt_client import MQTTClient
from mqtt_config import (
    CLIENT_ID_SMART_BUTTON,
    DEVICE_ID_BUTTON,
    ROOM_ZONE,
    TOPIC_BUTTON_EVENT,
)


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_payload(action_name):
    return {
        "device_id": DEVICE_ID_BUTTON,
        "type": "smart_button",
        "zone": ROOM_ZONE,
        "event": "pressed",
        "action": action_name,
        "ts": now_text(),
    }


def main():
    mqtt_client = MQTTClient(CLIENT_ID_SMART_BUTTON)
    mqtt_client.connect()

    print("[SMART BUTTON] SafeCore Smart Button started")
    print("[SMART BUTTON] Commands:")
    print("  1 = arm")
    print("  2 = disarm")
    print("  3 = reset_alarm")
    print("  q = quit")

    try:
        while True:
            command = input("Command: ").strip().lower()

            if command == "q":
                break
            elif command == "1":
                payload = build_payload("arm")
            elif command == "2":
                payload = build_payload("disarm")
            elif command == "3":
                payload = build_payload("reset_alarm")
            else:
                continue

            payload_text = json.dumps(payload)

            print(f"[SMART BUTTON] Sending: {payload_text}")
            mqtt_client.publish(TOPIC_BUTTON_EVENT, payload_text, qos=1)

    except KeyboardInterrupt:
        print("[SMART BUTTON] Stopping...")

    mqtt_client.disconnect()


if __name__ == "__main__":
    main()