# SafeCore_Project/models/mqtt_client.py

import paho.mqtt.client as mqtt

from mqtt_config import BROKER_HOST, BROKER_PORT, KEEPALIVE


class MQTTClient:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.is_connected = False

        self.message_callback = None
        self.connect_callback = None
        self.disconnect_callback = None

    def connect(self):
        print(f"[MQTT] Connecting to {BROKER_HOST}:{BROKER_PORT} as {self.client_id}...")
        self.client.connect(BROKER_HOST, BROKER_PORT, KEEPALIVE)
        self.client.loop_start()

    def disconnect(self):
        print("[MQTT] Disconnecting...")
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str, qos: int = 0):
        print(f"[MQTT] Subscribing to topic: {topic} | QoS={qos}")
        self.client.subscribe(topic, qos=qos)

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        print(f"[MQTT] Publishing to {topic}: {payload} | QoS={qos} | retain={retain}")
        self.client.publish(topic, payload, qos=qos, retain=retain)

    def set_message_callback(self, callback):
        self.message_callback = callback

    def set_connect_callback(self, callback):
        self.connect_callback = callback

    def set_disconnect_callback(self, callback):
        self.disconnect_callback = callback

    def _on_connect(self, client, userdata, flags, rc):
        self.is_connected = True
        print(f"[MQTT] Connected with result code {rc}")

        if self.connect_callback:
            self.connect_callback(rc)

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        print(f"[MQTT] Disconnected with result code {rc}")

        if self.disconnect_callback:
            self.disconnect_callback(rc)

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print(f"[MQTT] Message received on {msg.topic}: {payload}")

        if self.message_callback:
            self.message_callback(msg.topic, payload)