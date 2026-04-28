# SafeCore_Project/emulators/relay_controller.py

import json
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from models.mqtt_client import MQTTClient
from mqtt_config import (
    CLIENT_ID_RELAY_CONTROLLER,
    DEVICE_ID_RELAY,
    RELAY_TARGET_VENTILATION_FAN,
    RELAY_TARGET_ALARM_SIREN,
    VALID_RELAY_TARGETS,
    TOPIC_RELAY_COMMAND,
    TOPIC_RELAY_STATUS,
)


mqtt_client = None

relay_states = {
    RELAY_TARGET_VENTILATION_FAN: "off",
    RELAY_TARGET_ALARM_SIREN: "off",
}


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def publish_status(target):
    payload = {
        "device_id": DEVICE_ID_RELAY,
        "target": target,
        "state": relay_states[target],
        "ts": now_text(),
    }

    payload_text = json.dumps(payload)
    mqtt_client.publish(TOPIC_RELAY_STATUS, payload_text, qos=1)
    print(f"[RELAY] Status published: {payload_text}")


def publish_all_statuses():
    for target in VALID_RELAY_TARGETS:
        publish_status(target)


def handle_message(topic, payload):
    print(f"[RELAY] Command received: {payload}")

    try:
        data = json.loads(payload)

        target = data.get("target")
        command = data.get("command", "").lower()

        if target not in relay_states:
            print(f"[RELAY] Unknown target: {target}")
            return

        if command not in ["on", "off"]:
            print(f"[RELAY] Invalid command: {command}")
            return

        relay_states[target] = command
        print(f"[RELAY] {target} changed to {command.upper()}")

        publish_status(target)

    except Exception as e:
        print(f"[RELAY ERROR] {e}")


def main():
    global mqtt_client

    mqtt_client = MQTTClient(CLIENT_ID_RELAY_CONTROLLER)
    mqtt_client.set_message_callback(handle_message)
    mqtt_client.connect()
    mqtt_client.subscribe(TOPIC_RELAY_COMMAND, qos=1)

    print("[RELAY] SafeCore Relay Controller started")
    time.sleep(1)
    publish_all_statuses()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[RELAY] Stopping...")

    mqtt_client.disconnect()


if __name__ == "__main__":
    main()