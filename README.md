# SafeCore - IoT Monitoring & Control System

SafeCore is a final project for the course **Software Development for IoT Systems in a Smart City Environment**.

The project simulates a real-time IoT monitoring and control system for a critical facility room.  
The system monitors environmental and security conditions, detects abnormal situations, activates automatic responses, saves data locally, and displays the system status in a GUI dashboard.

---

## Project Links

> Replace the placeholders below with your real links before submitting.

- **GitHub Repository:** [SafeCore GitHub Repository](https://github.com/ShadiR94/SafeCore_IoT_Project)
- **Project Demo Video:** [Watch SafeCore Project Demo](https://drive.google.com/file/d/1cd12PQDDkPQro3WTsjDGmwTgiNpfY44l/view?usp=sharing)
- **Presentation Video:** [Watch SafeCore Presentation Video](https://drive.google.com/file/d/1RbunCM2BMDLK0B68ah-pjtgpN2ErjJIY/view?usp=sharing)

---

## Project Goal

The goal of SafeCore is to monitor a sensitive room in real time and react automatically to abnormal situations.

The system monitors:

- Temperature
- Humidity
- Door status
- Security mode
- Relay status
- Warnings
- Alarms

The system can automatically:

- Turn ON the ventilation fan when the temperature is too high.
- Turn OFF the ventilation fan when the temperature returns to normal.
- Detect door opening while the system is armed.
- Activate an alarm siren when intrusion is detected.
- Save telemetry, events, and alarms into a local SQLite database.
- Display the system status in a main GUI dashboard.
- Allow the user to control the system manually when needed.

---

## System Architecture

```text
Climate Sensor Emulator
Door Sensor Emulator
Smart Button Emulator
        |
        v
MQTT Broker
        |
        v
SafeCore Data Manager
        |
        +---- SQLite Database
        |
        +---- Warning / Alarm Logic
        |
        +---- Relay Commands
        |
        v
Relay Controller Emulator
        |
        v
Main GUI Dashboard
```

---

## Main Components

### 1. IoT Emulators

The project includes four IoT emulators:

| File | Description |
|---|---|
| `emulators/climate_sensor.py` | Sends temperature and humidity data |
| `emulators/door_sensor.py` | Sends door open / closed status |
| `emulators/smart_button.py` | Sends arm, disarm, and reset alarm commands |
| `emulators/relay_controller.py` | Receives relay commands and publishes relay status |

---

### 2. Data Manager

File:

```text
data_manager.py
```

The Data Manager is the core application of the system.

It is responsible for:

- Subscribing to MQTT topics.
- Receiving sensor data.
- Saving data into SQLite.
- Checking temperature and humidity thresholds.
- Detecting intrusion events.
- Publishing warning and alarm messages.
- Sending relay commands.
- Updating system state.

---

### 3. Main GUI Dashboard

File:

```text
main_gui.py
```

The GUI dashboard displays the current system status.

It shows:

- MQTT connection status
- Data Manager status
- Security mode
- Temperature
- Humidity
- Door status
- Ventilation fan status
- Alarm siren status
- Active alarm count
- Latest warning
- Latest alarm
- Event and alarm history

The GUI also allows the user to:

- Arm the system.
- Disarm the system.
- Reset alarm.
- Turn the fan ON/OFF manually.

---

### 4. Database

File:

```text
db.py
```

SafeCore uses a local SQLite database.

The database is created automatically under:

```text
database/safecore.db
```

The database includes the following tables:

| Table | Purpose |
|---|---|
| `telemetry` | Stores sensor and relay data |
| `events` | Stores system events |
| `alarms` | Stores alarm records |
| `system_state` | Stores the latest system state |

---

## MQTT Topics

The project uses MQTT topics under the SafeCore project root.

Examples:

```text
pr/critical_room/SR_1994_safecore/climate/status
pr/critical_room/SR_1994_safecore/door/status
pr/critical_room/SR_1994_safecore/button/event
pr/critical_room/SR_1994_safecore/relay/command
pr/critical_room/SR_1994_safecore/relay/status
pr/critical_room/SR_1994_safecore/system/command
pr/critical_room/SR_1994_safecore/system/mode/status
pr/critical_room/SR_1994_safecore/warning/status
pr/critical_room/SR_1994_safecore/alarm/status
pr/critical_room/SR_1994_safecore/manager/status
```

Important messages such as alarms, warnings, relay commands, relay status, and system commands use **QoS 1**.

---

## Requirements

The project requires Python 3 and the following packages:

```text
paho-mqtt
PyQt5
```

Install the requirements using:

```bash
pip install -r requirements.txt
```

---

## How to Run the Project

Open several terminal windows from the main project folder:

```text
SafeCore_Project/
```

### Step 1 - Install Requirements

```bash
pip install -r requirements.txt
```

### Step 2 - Run the Data Manager

```bash
python data_manager.py
```

The Data Manager connects to the MQTT broker, subscribes to the required topics, saves data to the database, and manages warnings and alarms.

### Step 3 - Run the Relay Controller

```bash
python emulators/relay_controller.py
```

The Relay Controller listens for relay commands and publishes relay status updates.

### Step 4 - Run the Main GUI

```bash
python main_gui.py
```

The GUI displays the system status and allows manual control.

### Step 5 - Run the Narrated Demo

```bash
python safecore_demo_narrated.py
```

This file runs the main demo flow automatically and gives time to explain each part during the presentation.

---

## Optional Manual Emulators

You can also run the emulators manually.

### Climate Sensor Emulator

```bash
python emulators/climate_sensor.py
```

Available commands:

```text
1 = normal climate data
2 = hot climate data
3 = humid climate data
Enter = send reading using current profile
q = quit
```

### Door Sensor Emulator

```bash
python emulators/door_sensor.py
```

Available commands:

```text
o = open door
c = close door
t / Enter = toggle door state
q = quit
```

### Smart Button Emulator

```bash
python emulators/smart_button.py
```

Available commands:

```text
1 = arm system
2 = disarm system
3 = reset_alarm
q = quit
```

---

## Demo Flow

The main demo shows the following flow:

1. The system starts in a normal state.
2. Normal temperature and humidity values are displayed.
3. High temperature is detected.
4. The ventilation fan turns ON automatically.
5. Temperature returns to normal.
6. The warning is cleared and the fan turns OFF.
7. High humidity is detected.
8. Humidity returns to normal and the warning is cleared.
9. The system changes to ARMED mode.
10. The door opens while the system is armed.
11. An intrusion alarm is created.
12. The alarm siren turns ON.
13. The user can manually DISARM and RESET ALARM from the GUI.
14. The system returns to a stable normal state.

---

## Demo Scenario 1 - High Temperature Warning

Expected result:

- Data Manager receives high temperature.
- Warning is created.
- Ventilation fan turns ON.
- Relay status is updated.
- GUI shows the warning and fan status.
- Data is saved in SQLite.

---

## Demo Scenario 2 - Intrusion Alarm

Expected result:

- System changes to ARMED mode.
- Door opens while system is armed.
- Data Manager creates an intrusion alarm.
- Alarm siren turns ON.
- GUI shows active alarm.
- Alarm is saved in SQLite.

---

## Demo Scenario 3 - Reset Alarm

Expected result:

- Alarm is cleared.
- Alarm siren turns OFF.
- GUI shows no active alarms.
- Event is saved in SQLite.

---

## Project Files Structure

```text
SafeCore_Project/
│
├── data_manager.py
├── db.py
├── main_gui.py
├── mqtt_config.py
├── requirements.txt
├── README.md
├── safecore_demo_narrated.py
│
├── models/
│   └── mqtt_client.py
│
└── emulators/
    ├── climate_sensor.py
    ├── door_sensor.py
    ├── smart_button.py
    └── relay_controller.py
```

---

## Notes

- The database file is created automatically.
- The system uses MQTT communication between all components.
- The project uses a local SQLite database.
- The GUI is built with PyQt5.
- QoS 1 is used for important messages such as alarms, warnings, relay commands, and system commands.
- The project is based on the course topics: MQTT, IoT emulators, GUI, event handling, database, warnings, and alarms.

---

## Author

Shadi Rabah  
Computer Science Student  
Final Project - IoT Systems in a Smart City Environment
