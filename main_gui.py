# SafeCore_Project/main_gui.py

import json
import sys
import time
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from db import init_db, get_current_states, get_recent_history, get_active_alarm_count
from models.mqtt_client import MQTTClient
from mqtt_config import (
    CLIENT_ID_GUI,
    MODE_ARMED,
    MODE_DISARMED,
    TOPIC_CLIMATE_STATUS,
    TOPIC_DOOR_STATUS,
    TOPIC_RELAY_STATUS,
    TOPIC_SYSTEM_MODE_STATUS,
    TOPIC_WARNING_STATUS,
    TOPIC_ALARM_STATUS,
    TOPIC_MANAGER_STATUS,
    TOPIC_SYSTEM_COMMAND,
    TOPIC_RELAY_COMMAND,
    RELAY_TARGET_VENTILATION_FAN,
    RELAY_TARGET_ALARM_SIREN,
)


class MainWindow(QMainWindow):
    mqtt_signal = pyqtSignal(str, str)
    mqtt_state_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.last_manager_heartbeat = 0
        self.last_history_snapshot = []

        self.current_mode = MODE_DISARMED
        self.current_temperature = "--"
        self.current_humidity = "--"
        self.current_door_state = "closed"
        self.current_fan_state = "off"
        self.current_siren_state = "off"

        self.last_warning_text = "No warnings yet"
        self.last_alarm_text = "No active alarms"
        self.last_alarm_active = False
        self.last_update_text = "--"

        init_db()

        self.setup_window()
        self.build_ui()
        self.setup_mqtt()
        self.load_initial_snapshot()
        self.setup_timers()
        self.update_button_styles()
        self.update_alert_panels()

    def setup_window(self):
        self.setWindowTitle("SafeCore")
        self.setMinimumSize(1380, 820)
        self.resize(1450, 860)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #eef2f7;
            }

            QWidget {
                font-family: Segoe UI, Arial, sans-serif;
                color: #1f2937;
                font-size: 14px;
            }

            QFrame#card {
                background-color: white;
                border: 1px solid #d9e2ec;
                border-radius: 18px;
            }

            QLabel#mainTitle {
                font-size: 34px;
                font-weight: bold;
                color: #0f172a;
            }

            QLabel#subTitle {
                font-size: 16px;
                color: #475569;
            }

            QLabel#sectionTitle {
                font-size: 19px;
                font-weight: bold;
                color: #0f172a;
            }

            QLabel#labelName {
                font-size: 14px;
                color: #475569;
            }

            QLabel#plainInfo {
                font-size: 14px;
                color: #0f172a;
                font-weight: 600;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 700;
                min-height: 40px;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QListWidget {
                background-color: white;
                border: none;
                padding: 8px;
                font-size: 13px;
            }
        """)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(18)

        title = QLabel("SafeCore")
        title.setObjectName("mainTitle")

        subtitle = QLabel("Real-Time IoT Monitoring & Control System for a Critical Facility Room")
        subtitle.setObjectName("subTitle")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        left_col = QVBoxLayout()
        left_col.setSpacing(18)
        left_col.addWidget(self.build_system_status_card(), 2)
        left_col.addWidget(self.build_alerts_card(), 2)

        middle_col = QVBoxLayout()
        middle_col.setSpacing(18)
        middle_col.addWidget(self.build_environment_card(), 2)
        middle_col.addWidget(self.build_security_card(), 2)

        right_col = QVBoxLayout()
        right_col.setSpacing(18)
        right_col.addWidget(self.build_controls_card(), 2)
        right_col.addWidget(self.build_history_card(), 4)

        content_layout.addLayout(left_col, 4)
        content_layout.addLayout(middle_col, 4)
        content_layout.addLayout(right_col, 5)

        main_layout.addLayout(content_layout)

    def build_system_status_card(self):
        frame = self.create_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("System Status")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        self.mode_badge = self.create_badge_label()
        self.mqtt_badge = self.create_badge_label()
        self.manager_badge = self.create_badge_label()
        self.active_alarm_badge = self.create_badge_label()
        self.last_update_value = self.create_plain_value("--")

        rows = [
            ("Security Mode", self.mode_badge),
            ("MQTT Status", self.mqtt_badge),
            ("Data Manager", self.manager_badge),
            ("Active Alarm Count", self.active_alarm_badge),
            ("Last Update", self.last_update_value),
        ]

        for row_index, (label_text, widget) in enumerate(rows):
            label = QLabel(label_text)
            label.setObjectName("labelName")
            grid.addWidget(label, row_index, 0)
            grid.addWidget(widget, row_index, 1)

        layout.addLayout(grid)
        return frame

    def build_environment_card(self):
        frame = self.create_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("Environment")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        self.temp_value = self.create_plain_value("-- C")
        self.humidity_value = self.create_plain_value("-- %")
        self.fan_badge = self.create_badge_label()

        rows = [
            ("Temperature", self.temp_value),
            ("Humidity", self.humidity_value),
            ("Ventilation Fan", self.fan_badge),
        ]

        for row_index, (label_text, widget) in enumerate(rows):
            label = QLabel(label_text)
            label.setObjectName("labelName")
            grid.addWidget(label, row_index, 0)
            grid.addWidget(widget, row_index, 1)

        layout.addLayout(grid)
        return frame

    def build_security_card(self):
        frame = self.create_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("Security")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)

        self.door_badge = self.create_badge_label()
        self.siren_badge = self.create_badge_label()

        rows = [
            ("Door Status", self.door_badge),
            ("Alarm Siren", self.siren_badge),
        ]

        for row_index, (label_text, widget) in enumerate(rows):
            label = QLabel(label_text)
            label.setObjectName("labelName")
            grid.addWidget(label, row_index, 0)
            grid.addWidget(widget, row_index, 1)

        layout.addLayout(grid)
        return frame

    def build_alerts_card(self):
        frame = self.create_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("Alerts Panel")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.warning_panel, self.warning_text = self.create_alert_panel("Latest Warning")
        self.alarm_panel, self.alarm_text = self.create_alert_panel("Latest Alarm")

        layout.addWidget(self.warning_panel)
        layout.addWidget(self.alarm_panel)

        return frame

    def build_controls_card(self):
        frame = self.create_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("Controls")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self.arm_button = QPushButton("ARM")
        self.disarm_button = QPushButton("DISARM")
        self.reset_alarm_button = QPushButton("RESET ALARM")
        self.fan_toggle_button = QPushButton("FAN ON")

        self.arm_button.clicked.connect(lambda: self.send_system_command("set_mode", MODE_ARMED))
        self.disarm_button.clicked.connect(lambda: self.send_system_command("set_mode", MODE_DISARMED))
        self.reset_alarm_button.clicked.connect(lambda: self.send_system_command("reset_alarm"))
        self.fan_toggle_button.clicked.connect(self.handle_fan_toggle)

        grid.addWidget(self.arm_button, 0, 0)
        grid.addWidget(self.disarm_button, 0, 1)
        grid.addWidget(self.reset_alarm_button, 1, 0, 1, 2)
        grid.addWidget(self.fan_toggle_button, 2, 0, 1, 2)

        layout.addLayout(grid)
        return frame

    def build_history_card(self):
        frame = self.create_card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("Event & Alarm Log")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.history_list = QListWidget()
        history_font = QFont("Consolas", 10)
        self.history_list.setFont(history_font)

        layout.addWidget(self.history_list)
        return frame

    def create_card(self):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return frame

    def create_badge_label(self):
        label = QLabel("--")
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(30)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                background-color: #e5e7eb;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 6px 12px;
                font-weight: 700;
            }
        """)
        return label

    def create_plain_value(self, text):
        label = QLabel(text)
        label.setObjectName("plainInfo")
        label.setWordWrap(True)
        return label

    def create_alert_panel(self, title_text):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #d9e2ec;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #0f172a;")
        layout.addWidget(title)

        text_label = QLabel("No data")
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #0f172a;")
        layout.addWidget(text_label)

        return panel, text_label

    def set_badge(self, label, text, badge_type):
        styles = {
            "good": ("#dcfce7", "#166534", "#bbf7d0"),
            "info": ("#dbeafe", "#1d4ed8", "#bfdbfe"),
            "warning": ("#fef3c7", "#92400e", "#fde68a"),
            "danger": ("#fee2e2", "#b91c1c", "#fecaca"),
            "neutral": ("#e5e7eb", "#374151", "#d1d5db"),
        }

        background, color, border = styles.get(badge_type, styles["neutral"])

        label.setText(text)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {background};
                color: {color};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 6px 12px;
                font-weight: 700;
            }}
        """)

    def set_alert_style(self, panel, text_label, panel_type, text):
        if panel_type == "warning":
            bg = "#fffbeb"
            border = "#fcd34d"
            color = "#92400e"
        elif panel_type == "danger":
            bg = "#fef2f2"
            border = "#fca5a5"
            color = "#b91c1c"
        else:
            bg = "#f8fafc"
            border = "#d9e2ec"
            color = "#0f172a"

        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 14px;
            }}
        """)
        text_label.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {color};")
        text_label.setText(text)

    def style_button_blue(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 700;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

    def style_button_gray(self, button):
        button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 700;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)

    def update_button_styles(self):
        if self.current_mode == MODE_ARMED:
            self.style_button_gray(self.arm_button)
            self.style_button_blue(self.disarm_button)
        else:
            self.style_button_blue(self.arm_button)
            self.style_button_gray(self.disarm_button)

        if self.current_fan_state == "on":
            self.fan_toggle_button.setText("FAN OFF")
            self.style_button_gray(self.fan_toggle_button)
        else:
            self.fan_toggle_button.setText("FAN ON")
            self.style_button_blue(self.fan_toggle_button)

        self.style_button_blue(self.reset_alarm_button)

    def handle_fan_toggle(self):
        if self.current_fan_state == "on":
            command = "off"
        else:
            command = "on"

        payload = {
            "target": RELAY_TARGET_VENTILATION_FAN,
            "command": command,
            "reason": "manual_fan_test",
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self.mqtt_client.publish(TOPIC_RELAY_COMMAND, json.dumps(payload), qos=1)

    def setup_mqtt(self):
        self.mqtt_client = MQTTClient(CLIENT_ID_GUI)
        self.mqtt_client.set_message_callback(self.on_mqtt_message)
        self.mqtt_client.set_connect_callback(self.on_mqtt_connect)
        self.mqtt_client.set_disconnect_callback(self.on_mqtt_disconnect)
        self.mqtt_client.connect()

        self.mqtt_client.subscribe(TOPIC_CLIMATE_STATUS, qos=1)
        self.mqtt_client.subscribe(TOPIC_DOOR_STATUS, qos=1)
        self.mqtt_client.subscribe(TOPIC_RELAY_STATUS, qos=1)
        self.mqtt_client.subscribe(TOPIC_SYSTEM_MODE_STATUS, qos=1)
        self.mqtt_client.subscribe(TOPIC_WARNING_STATUS, qos=1)
        self.mqtt_client.subscribe(TOPIC_ALARM_STATUS, qos=1)
        self.mqtt_client.subscribe(TOPIC_MANAGER_STATUS)

        self.mqtt_signal.connect(self.handle_mqtt_message)
        self.mqtt_state_signal.connect(self.handle_mqtt_state)

    def setup_timers(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_runtime_data)
        self.refresh_timer.start(2000)

    def load_initial_snapshot(self):
        states = get_current_states()

        self.current_mode = states.get("security_mode", MODE_DISARMED)
        self.current_temperature = states.get("temperature", "--")
        self.current_humidity = states.get("humidity", "--")
        self.current_door_state = states.get("door_state", "closed")
        self.current_fan_state = states.get("relay_ventilation_fan", "off")
        self.current_siren_state = states.get("relay_alarm_siren", "off")

        self.last_warning_text = states.get("last_warning", "No warnings yet")
        self.last_alarm_text = states.get("last_alarm", "No active alarms")
        self.last_update_text = states.get("last_update", "--")

        self.temp_value.setText(f"{self.current_temperature} C")
        self.humidity_value.setText(f"{self.current_humidity} %")
        self.last_update_value.setText(self.last_update_text)

        self.apply_status_badges()
        self.warning_text.setText(self.last_warning_text)
        self.alarm_text.setText(self.last_alarm_text)

    def on_mqtt_connect(self, rc):
        self.mqtt_state_signal.emit("connected")

    def on_mqtt_disconnect(self, rc):
        self.mqtt_state_signal.emit("disconnected")

    def handle_mqtt_state(self, state):
        if state == "connected":
            self.set_badge(self.mqtt_badge, "Connected", "good")
        else:
            self.set_badge(self.mqtt_badge, "Disconnected", "danger")

    def on_mqtt_message(self, topic, payload):
        self.mqtt_signal.emit(topic, payload)

    def handle_mqtt_message(self, topic, payload):
        try:
            data = json.loads(payload)
        except Exception:
            return

        message_time = data.get("ts", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.last_update_text = message_time.split(" ")[1] if " " in message_time else message_time
        self.last_update_value.setText(self.last_update_text)

        if topic == TOPIC_CLIMATE_STATUS:
            self.current_temperature = data.get("temperature", "--")
            self.current_humidity = data.get("humidity", "--")
            self.temp_value.setText(f"{self.current_temperature} C")
            self.humidity_value.setText(f"{self.current_humidity} %")

        elif topic == TOPIC_DOOR_STATUS:
            self.current_door_state = data.get("door_state", "closed")

        elif topic == TOPIC_RELAY_STATUS:
            target = data.get("target")
            state = data.get("state", "off").lower()

            if target == RELAY_TARGET_VENTILATION_FAN:
                self.current_fan_state = state
            elif target == RELAY_TARGET_ALARM_SIREN:
                self.current_siren_state = state
            else:
                print(f"[GUI] Unknown relay target received: {target}")

        elif topic == TOPIC_SYSTEM_MODE_STATUS:
            self.current_mode = data.get("mode", MODE_DISARMED)

        elif topic == TOPIC_WARNING_STATUS:
            warning_active = data.get("is_active", 1) == 1

            if warning_active:
                self.last_warning_text = data.get("message", "Warning received")
            else:
                self.last_warning_text = "No warnings yet"

        elif topic == TOPIC_ALARM_STATUS:
            self.last_alarm_active = data.get("is_active", 1) == 1

            if self.last_alarm_active:
                self.last_alarm_text = data.get("message", "Alarm received")
            else:
                self.last_alarm_text = "No active alarms"

        elif topic == TOPIC_MANAGER_STATUS:
            self.last_manager_heartbeat = time.time()

        self.apply_status_badges()
        self.update_button_styles()
        self.update_alert_panels()

    def apply_status_badges(self):
        if self.current_mode == MODE_ARMED:
            self.set_badge(self.mode_badge, "ARMED", "danger")
        else:
            self.set_badge(self.mode_badge, "DISARMED", "good")

        if str(self.current_door_state).lower() == "open":
            self.set_badge(self.door_badge, "OPEN", "warning")
        else:
            self.set_badge(self.door_badge, "CLOSED", "good")

        if self.current_fan_state == "on":
            self.set_badge(self.fan_badge, "ON", "info")
        else:
            self.set_badge(self.fan_badge, "OFF", "neutral")

        if self.current_siren_state == "on":
            self.set_badge(self.siren_badge, "ON", "danger")
        else:
            self.set_badge(self.siren_badge, "OFF", "neutral")

        active_alarm_count = get_active_alarm_count()
        if active_alarm_count > 0:
            self.set_badge(self.active_alarm_badge, str(active_alarm_count), "danger")
        else:
            self.set_badge(self.active_alarm_badge, "0", "good")

    def update_alert_panels(self):
        if self.last_warning_text.strip().lower() == "no warnings yet":
            self.set_alert_style(self.warning_panel, self.warning_text, "neutral", self.last_warning_text)
        else:
            self.set_alert_style(self.warning_panel, self.warning_text, "warning", self.last_warning_text)

        if get_active_alarm_count() > 0 or self.last_alarm_active:
            self.set_alert_style(self.alarm_panel, self.alarm_text, "danger", self.last_alarm_text)
        else:
            self.set_alert_style(self.alarm_panel, self.alarm_text, "neutral", self.last_alarm_text)

    def refresh_runtime_data(self):
        if time.time() - self.last_manager_heartbeat > 8:
            self.set_badge(self.manager_badge, "Waiting...", "warning")
        else:
            self.set_badge(self.manager_badge, "Online", "good")

        self.apply_status_badges()
        self.update_button_styles()
        self.update_alert_panels()

        history_items = get_recent_history(20)

        if history_items != self.last_history_snapshot:
            self.last_history_snapshot = history_items
            self.history_list.clear()

            for item in history_items:
                self.history_list.addItem(QListWidgetItem(item))

    def send_system_command(self, action, mode=None):
        payload = {
            "action": action,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if mode:
            payload["mode"] = mode

        self.mqtt_client.publish(TOPIC_SYSTEM_COMMAND, json.dumps(payload), qos=1)

    def closeEvent(self, event):
        try:
            self.mqtt_client.disconnect()
        except Exception:
            pass

        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()