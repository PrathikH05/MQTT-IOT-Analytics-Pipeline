import json
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "sensors/temperature"

message = {
    "sensor_id": "TEMP-01",
    "sensor_type": "temperature",
    "value": 28.5,
    "unit": "C",
    "location": "Plant-A",
    "reading_timestamp": datetime.now().isoformat(timespec="seconds")
}

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="python-test-publisher"
)

client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
client.loop_start()

result = client.publish(TOPIC, json.dumps(message), qos=1)
result.wait_for_publish()

print(f"Published to {TOPIC}")
print(json.dumps(message, indent=2))

client.loop_stop()
client.disconnect()