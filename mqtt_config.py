# SafeCore_Project/mqtt_config.py

# =========================================
# MQTT Broker Configuration
# =========================================
BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
KEEPALIVE = 60

# =========================================
# Project Identity
# =========================================
PROJECT_NAME = "SafeCore"
PROJECT_ID = "SR_1994_safecore"

# Root topic for all system messages
TOPIC_ROOT = f"pr/critical_room/{PROJECT_ID}"

# =========================================
# System Modes
# =========================================
MODE_ARMED = "armed"
MODE_DISARMED = "disarmed"
DEFAULT_SECURITY_MODE = MODE_DISARMED

VALID_SECURITY_MODES = [MODE_ARMED, MODE_DISARMED]

# =========================================
# Relay Targets
# =========================================
RELAY_TARGET_VENTILATION_FAN = "ventilation_fan"
RELAY_TARGET_ALARM_SIREN = "alarm_siren"

VALID_RELAY_TARGETS = [
    RELAY_TARGET_VENTILATION_FAN,
    RELAY_TARGET_ALARM_SIREN,
]

# =========================================
# Climate Thresholds
# =========================================
TEMP_THRESHOLD = 30.0
TEMP_RESET_THRESHOLD = 27.5

HUMIDITY_THRESHOLD = 70.0
HUMIDITY_RESET_THRESHOLD = 60.0

# =========================================
# Topics - Sensor Status / Events
# =========================================
TOPIC_CLIMATE_STATUS = f"{TOPIC_ROOT}/climate/sts"
TOPIC_DOOR_STATUS = f"{TOPIC_ROOT}/door/sts"
TOPIC_BUTTON_EVENT = f"{TOPIC_ROOT}/button/evt"

# =========================================
# Topics - Relay
# =========================================
TOPIC_RELAY_COMMAND = f"{TOPIC_ROOT}/relay/cmd"
TOPIC_RELAY_STATUS = f"{TOPIC_ROOT}/relay/sts"

# =========================================
# Topics - System / Manager / Alerts
# =========================================
TOPIC_SYSTEM_COMMAND = f"{TOPIC_ROOT}/system/cmd"
TOPIC_SYSTEM_MODE_STATUS = f"{TOPIC_ROOT}/system/mode/sts"
TOPIC_WARNING_STATUS = f"{TOPIC_ROOT}/warning/sts"
TOPIC_ALARM_STATUS = f"{TOPIC_ROOT}/alarm/sts"
TOPIC_MANAGER_STATUS = f"{TOPIC_ROOT}/manager/status"

# =========================================
# Client IDs
# =========================================
CLIENT_ID_MANAGER = f"{PROJECT_ID}_manager"
CLIENT_ID_GUI = f"{PROJECT_ID}_gui"
CLIENT_ID_CLIMATE_SENSOR = f"{PROJECT_ID}_climate_sensor"
CLIENT_ID_DOOR_SENSOR = f"{PROJECT_ID}_door_sensor"
CLIENT_ID_SMART_BUTTON = f"{PROJECT_ID}_smart_button"
CLIENT_ID_RELAY_CONTROLLER = f"{PROJECT_ID}_relay_controller"

# =========================================
# Database
# =========================================
DB_FOLDER = "database"
DB_FILE_NAME = "safecore.db"

# =========================================
# Room / Device Identity
# =========================================
ROOM_NAME = "Critical Facility Room"
ROOM_ZONE = "critical_room_01"

DEVICE_ID_CLIMATE = "climate_01"
DEVICE_ID_DOOR = "door_01"
DEVICE_ID_BUTTON = "button_01"
DEVICE_ID_RELAY = "relay_01"