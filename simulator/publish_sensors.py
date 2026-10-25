import json
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
PUBLISH_INTERVAL_SECONDS = 3

SENSORS = [
    {
        "sensor_id": "TEMP-01",
        "sensor_type": "temperature",
        "unit": "C",
        "location": "Plant-A",
        "normal_min": 20.0,
        "normal_max": 45.0,
        "anomaly_min": 65.0,
        "anomaly_max": 85.0,
    },
    {
        "sensor_id": "HUM-01",
        "sensor_type": "humidity",
        "unit": "%",
        "location": "Plant-A",
        "normal_min": 35.0,
        "normal_max": 70.0,
        "anomaly_min": 85.0,
        "anomaly_max": 98.0,
    },
    {
        "sensor_id": "VIB-01",
        "sensor_type": "vibration",
        "unit": "mm/s",
        "location": "Plant-B",
        "normal_min": 0.5,
        "normal_max": 4.5,
        "anomaly_min": 7.0,
        "anomaly_max": 12.0,
    },
]


def generate_reading(sensor):
    is_anomaly = random.random() < 0.10

    if is_anomaly:
        value = random.uniform(sensor["anomaly_min"], sensor["anomaly_max"])
    else:
        value = random.uniform(sensor["normal_min"], sensor["normal_max"])

    return {
        "sensor_id": sensor["sensor_id"],
        "sensor_type": sensor["sensor_type"],
        "value": round(value, 2),
        "unit": sensor["unit"],
        "location": sensor["location"],
        "reading_timestamp": datetime.now().isoformat(timespec="seconds"),
        "is_simulated_anomaly": is_anomaly,
    }


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"MQTT connection failed. Reason code: {reason_code}")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="industrial-sensor-simulator",
)
client.on_connect = on_connect

client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

print("Sensor simulator started. Press Ctrl + C to stop.")

try:
    while True:
        for sensor in SENSORS:
            reading = generate_reading(sensor)
            topic = f"sensors/{sensor['sensor_type']}"

            result = client.publish(topic, json.dumps(reading), qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "ANOMALY" if reading["is_simulated_anomaly"] else "normal"
                print(
                    f"[{status.upper():7}] "
                    f"{topic:<22} "
                    f"{reading['sensor_id']}: "
                    f"{reading['value']} {reading['unit']}"
                )
            else:
                print(f"Publish failed for {sensor['sensor_id']}")

        time.sleep(PUBLISH_INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("\nStopping sensor simulator...")

finally:
    client.loop_stop()
    client.disconnect()
    print("Disconnected from MQTT broker.")