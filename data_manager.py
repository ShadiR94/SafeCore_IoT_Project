# SafeCore_Project/data_manager.py

import json
import time
from datetime import datetime

from db import (
    init_db,
    save_telemetry,
    save_event,
    save_alarm,
    set_system_state,
)
from models.mqtt_client import MQTTClient
from mqtt_config import (
    CLIENT_ID_MANAGER,
    DEFAULT_SECURITY_MODE,
    MODE_ARMED,
    MODE_DISARMED,
    DEVICE_ID_CLIMATE,
    DEVICE_ID_DOOR,
    DEVICE_ID_BUTTON,
    DEVICE_ID_RELAY,
    ROOM_ZONE,
    RELAY_TARGET_VENTILATION_FAN,
    RELAY_TARGET_ALARM_SIREN,
    TOPIC_CLIMATE_STATUS,
    TOPIC_DOOR_STATUS,
    TOPIC_BUTTON_EVENT,
    TOPIC_RELAY_COMMAND,
    TOPIC_RELAY_STATUS,
    TOPIC_SYSTEM_COMMAND,
    TOPIC_SYSTEM_MODE_STATUS,
    TOPIC_WARNING_STATUS,
    TOPIC_ALARM_STATUS,
    TOPIC_MANAGER_STATUS,
    TEMP_THRESHOLD,
    TEMP_RESET_THRESHOLD,
    HUMIDITY_THRESHOLD,
    HUMIDITY_RESET_THRESHOLD,
)


mqtt_client = None

current_security_mode = DEFAULT_SECURITY_MODE
current_door_state = "closed"

latest_temperature = None
latest_humidity = None

high_temp_active = False
high_humidity_active = False
intrusion_alarm_active = False

relay_states = {
    RELAY_TARGET_VENTILATION_FAN: "off",
    RELAY_TARGET_ALARM_SIREN: "off",
}


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def publish_json(topic, data, qos=0, retain=False):
    mqtt_client.publish(topic, json.dumps(data), qos=qos, retain=retain)


def init_default_states():
    set_system_state("security_mode", DEFAULT_SECURITY_MODE)
    set_system_state("door_state", "closed")
    set_system_state("temperature", "--")
    set_system_state("humidity", "--")
    set_system_state("relay_ventilation_fan", "off")
    set_system_state("relay_alarm_siren", "off")
    set_system_state("last_warning", "No warnings yet")
    set_system_state("last_alarm", "No active alarms")
    set_system_state("last_update", "--")


def publish_warning_status(message, is_active):
    payload = {
        "warning_code": "ENVIRONMENT",
        "zone": ROOM_ZONE,
        "message": message,
        "is_active": is_active,
        "ts": now_text(),
    }

    set_system_state("last_warning", message)
    publish_json(TOPIC_WARNING_STATUS, payload, qos=1)

    print(f"[WARNING STATUS] {message}")


def refresh_warning_status():
    if high_temp_active:
        message = f"High temperature detected: {latest_temperature} C"
        publish_warning_status(message, 1)
    elif high_humidity_active:
        message = f"High humidity detected: {latest_humidity}%"
        publish_warning_status(message, 1)
    else:
        publish_warning_status("No warnings yet", 0)


def publish_alarm_status(message, is_active, severity="critical"):
    payload = {
        "alarm_code": "INTRUSION",
        "severity": severity,
        "zone": ROOM_ZONE,
        "message": message,
        "is_active": is_active,
        "ts": now_text(),
    }

    set_system_state("last_alarm", message)
    publish_json(TOPIC_ALARM_STATUS, payload, qos=1)

    print(f"[ALARM STATUS] {message}")


def set_security_mode(new_mode, source_name):
    global current_security_mode

    new_mode = new_mode.lower()

    if new_mode == current_security_mode:
        print(f"[MODE] System already in {new_mode.upper()} mode")
        return

    current_security_mode = new_mode
    set_system_state("security_mode", current_security_mode)

    message = f"Security mode changed to {current_security_mode.upper()} by {source_name}"
    save_event("INFO", "MODE", ROOM_ZONE, message)

    payload = {
        "mode": current_security_mode,
        "source": source_name,
        "ts": now_text(),
    }

    publish_json(TOPIC_SYSTEM_MODE_STATUS, payload, qos=1)
    print(f"[MODE] {message}")


def send_relay_command(target, command, reason):
    payload = {
        "device_id": DEVICE_ID_RELAY,
        "target": target,
        "command": command.lower(),
        "reason": reason,
        "ts": now_text(),
    }

    publish_json(TOPIC_RELAY_COMMAND, payload, qos=1)
    print(f"[ACTION] Relay command sent -> {target}: {command} ({reason})")


def clear_intrusion_alarm(event_source_name, relay_reason):
    global intrusion_alarm_active

    if not intrusion_alarm_active:
        save_event("INFO", event_source_name, ROOM_ZONE, "Reset alarm requested but no active alarm")
        print("[INFO] Reset alarm requested but no active alarm")
        return

    if current_security_mode == MODE_ARMED and current_door_state == "open":
        save_event(
            "INFO",
            event_source_name,
            ROOM_ZONE,
            "Alarm reset denied: close door or disarm system first"
        )
        print("[INFO] Alarm reset denied: close door or disarm system first")
        return

    intrusion_alarm_active = False

    save_event("INFO", event_source_name, ROOM_ZONE, "Alarm reset by user")
    save_alarm("INTRUSION", "info", ROOM_ZONE, "Intrusion alarm reset by user", 0)

    publish_alarm_status("No active alarms", 0, "info")
    send_relay_command(RELAY_TARGET_ALARM_SIREN, "off", relay_reason)

    print("[INFO] Intrusion alarm reset by user")


def handle_climate_message(payload):
    global latest_temperature, latest_humidity
    global high_temp_active, high_humidity_active

    data = json.loads(payload)

    device_id = data.get("device_id", DEVICE_ID_CLIMATE)
    temperature = data.get("temperature")
    humidity = data.get("humidity")

    latest_temperature = temperature
    latest_humidity = humidity

    save_telemetry(
        device_id=device_id,
        device_type="climate_sensor",
        zone=ROOM_ZONE,
        temperature=temperature,
        humidity=humidity,
        status_text="environment_update",
    )

    set_system_state("temperature", temperature)
    set_system_state("humidity", humidity)

    print(f"[DB] Climate data saved: temp={temperature}, humidity={humidity}")

    if temperature is not None:
        if temperature >= TEMP_THRESHOLD and not high_temp_active:
            high_temp_active = True

            message = f"High temperature detected: {temperature} C"
            save_event("WARNING", "HIGH_TEMPERATURE", ROOM_ZONE, message)
            send_relay_command(RELAY_TARGET_VENTILATION_FAN, "on", "high_temperature")
            print(f"[WARNING] {message}")

        elif temperature <= TEMP_RESET_THRESHOLD and high_temp_active:
            high_temp_active = False

            message = f"Temperature returned to normal: {temperature} C"
            save_event("INFO", "CLIMATE", ROOM_ZONE, message)
            send_relay_command(RELAY_TARGET_VENTILATION_FAN, "off", "temperature_normal")
            print(f"[INFO] {message}")

    if humidity is not None:
        if humidity >= HUMIDITY_THRESHOLD and not high_humidity_active:
            high_humidity_active = True

            message = f"High humidity detected: {humidity}%"
            save_event("WARNING", "HIGH_HUMIDITY", ROOM_ZONE, message)
            print(f"[WARNING] {message}")

        elif humidity <= HUMIDITY_RESET_THRESHOLD and high_humidity_active:
            high_humidity_active = False

            message = f"Humidity returned to normal: {humidity}%"
            save_event("INFO", "CLIMATE", ROOM_ZONE, message)
            print(f"[INFO] {message}")

    refresh_warning_status()


def handle_door_message(payload):
    global current_door_state
    global intrusion_alarm_active

    data = json.loads(payload)

    device_id = data.get("device_id", DEVICE_ID_DOOR)
    door_state = data.get("door_state", "closed").lower()

    current_door_state = door_state

    save_telemetry(
        device_id=device_id,
        device_type="door_sensor",
        zone=ROOM_ZONE,
        status_text=door_state,
    )

    set_system_state("door_state", door_state)
    print(f"[DB] Door state saved: {door_state}")

    if door_state == "open":
        if current_security_mode == MODE_ARMED:
            if not intrusion_alarm_active:
                intrusion_alarm_active = True

                message = "Unauthorized door opening detected while system is ARMED"
                save_alarm("INTRUSION", "critical", ROOM_ZONE, message, 1)
                publish_alarm_status(message, 1, "critical")
                send_relay_command(RELAY_TARGET_ALARM_SIREN, "on", "intrusion_detected")
        else:
            message = "Authorized access: door opened while system is DISARMED"
            save_event("INFO", "DOOR", ROOM_ZONE, message)
            print(f"[INFO] {message}")

    elif door_state == "closed":
        message = "Door closed"
        save_event("INFO", "DOOR", ROOM_ZONE, message)
        print(f"[INFO] {message}")


def handle_button_event(payload):
    data = json.loads(payload)

    device_id = data.get("device_id", DEVICE_ID_BUTTON)
    action = data.get("action", "").lower()

    save_telemetry(
        device_id=device_id,
        device_type="smart_button",
        zone=ROOM_ZONE,
        status_text=action,
    )

    print(f"[DB] Button event saved: {action}")

    if action == "arm":
        set_security_mode(MODE_ARMED, "smart_button")

    elif action == "disarm":
        set_security_mode(MODE_DISARMED, "smart_button")

    elif action == "reset_alarm":
        clear_intrusion_alarm("BUTTON", "manual_alarm_reset")


def handle_relay_status(payload):
    data = json.loads(payload)

    target = data.get("target")
    state = data.get("state", "off").lower()

    if target not in relay_states:
        print(f"[RELAY] Unknown relay target received: {target}")
        return

    relay_states[target] = state
    set_system_state(f"relay_{target}", state)

    save_telemetry(
        device_id=DEVICE_ID_RELAY,
        device_type="relay_controller",
        zone=target,
        status_text=state,
    )

    print(f"[DB] Relay status saved -> {target}: {state}")


def handle_system_command(payload):
    data = json.loads(payload)

    action = data.get("action", "").lower()
    requested_mode = data.get("mode", "").lower()

    print(f"[SYSTEM] Command received: {action}")

    if action == "set_mode" and requested_mode in [MODE_ARMED, MODE_DISARMED]:
        set_security_mode(requested_mode, "gui")

    elif action == "reset_alarm":
        clear_intrusion_alarm("GUI", "gui_alarm_reset")


def handle_message(topic, payload):
    try:
        set_system_state("last_update", now_text())

        if topic == TOPIC_CLIMATE_STATUS:
            handle_climate_message(payload)

        elif topic == TOPIC_DOOR_STATUS:
            handle_door_message(payload)

        elif topic == TOPIC_BUTTON_EVENT:
            handle_button_event(payload)

        elif topic == TOPIC_RELAY_STATUS:
            handle_relay_status(payload)

        elif topic == TOPIC_SYSTEM_COMMAND:
            handle_system_command(payload)

        else:
            print(f"[MANAGER] Unhandled topic: {topic}")

    except Exception as e:
        print(f"[ERROR] Failed to process message on {topic}: {e}")


def heartbeat_loop():
    while True:
        payload = {
            "status": "alive",
            "security_mode": current_security_mode,
            "ts": now_text(),
        }

        try:
            publish_json(TOPIC_MANAGER_STATUS, payload)
        except Exception as e:
            print(f"[HEARTBEAT ERROR] {e}")

        time.sleep(4)


def main():
    global mqtt_client

    print("Starting SafeCore Data Manager...")

    init_db()
    init_default_states()

    mqtt_client = MQTTClient(CLIENT_ID_MANAGER)
    mqtt_client.set_message_callback(handle_message)
    mqtt_client.connect()

    mqtt_client.subscribe(TOPIC_CLIMATE_STATUS, qos=1)
    mqtt_client.subscribe(TOPIC_DOOR_STATUS, qos=1)
    mqtt_client.subscribe(TOPIC_BUTTON_EVENT, qos=1)
    mqtt_client.subscribe(TOPIC_RELAY_STATUS, qos=1)
    mqtt_client.subscribe(TOPIC_SYSTEM_COMMAND, qos=1)

    set_security_mode(DEFAULT_SECURITY_MODE, "system")
    refresh_warning_status()
    publish_alarm_status("No active alarms", 0, "info")

    try:
        heartbeat_loop()
    except KeyboardInterrupt:
        print("Stopping SafeCore Data Manager...")
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()