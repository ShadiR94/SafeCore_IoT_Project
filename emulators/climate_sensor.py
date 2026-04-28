# SafeCore_Project/emulators/climate_sensor.py

import json
import random
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from models.mqtt_client import MQTTClient
from mqtt_config import (
    CLIENT_ID_CLIMATE_SENSOR,
    DEVICE_ID_CLIMATE,
    ROOM_ZONE,
    TOPIC_CLIMATE_STATUS,
)


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_climate(profile_name):
    if profile_name == "hot":
        temperature = round(random.uniform(30.5, 34.0), 2)
        humidity = round(random.uniform(45.0, 58.0), 2)

    elif profile_name == "humid":
        temperature = round(random.uniform(24.0, 28.0), 2)
        humidity = round(random.uniform(71.0, 82.0), 2)

    elif profile_name == "normal":
        temperature = round(random.uniform(23.0, 27.0), 2)
        humidity = round(random.uniform(40.0, 58.0), 2)

    else:
        temperature = round(random.uniform(22.0, 26.0), 2)
        humidity = round(random.uniform(40.0, 55.0), 2)

    return temperature, humidity


def main():
    mqtt_client = MQTTClient(CLIENT_ID_CLIMATE_SENSOR)
    mqtt_client.connect()

    current_profile = "normal"

    print("[CLIMATE SENSOR] SafeCore Climate Sensor started")
    print("[CLIMATE SENSOR] Commands:")
    print("  1 = normal")
    print("  2 = hot")
    print("  3 = humid")
    print("  Enter = send reading using current profile")
    print("  q = quit")

    try:
        while True:
            command = input("Command: ").strip().lower()

            if command == "q":
                break
            elif command == "1":
                current_profile = "normal"
            elif command == "2":
                current_profile = "hot"
            elif command == "3":
                current_profile = "humid"

            temperature, humidity = generate_climate(current_profile)

            payload = {
                "device_id": DEVICE_ID_CLIMATE,
                "type": "climate_sensor",
                "zone": ROOM_ZONE,
                "temperature": temperature,
                "humidity": humidity,
                "ts": now_text(),
            }

            payload_text = json.dumps(payload)

            print(f"[CLIMATE SENSOR] Sending: {payload_text}")
            mqtt_client.publish(TOPIC_CLIMATE_STATUS, payload_text, qos=1)

    except KeyboardInterrupt:
        print("[CLIMATE SENSOR] Stopping...")

    mqtt_client.disconnect()


if __name__ == "__main__":
    main()