import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt
import psycopg

BROKER_HOST = "localhost"
BROKER_PORT = 1883
MQTT_TOPIC = "sensors/#"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "iot_pipeline",
    "user": "iot_user",
    "password": "iot_pass",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def get_database_connection():
    return psycopg.connect(**DB_CONFIG)


def insert_sensor_reading(payload):
    reading_timestamp = datetime.fromisoformat(payload["reading_timestamp"])

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw_sensor_data (
                    sensor_id,
                    sensor_type,
                    value,
                    unit,
                    location,
                    reading_timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    payload["sensor_id"],
                    payload["sensor_type"],
                    payload["value"],
                    payload["unit"],
                    payload["location"],
                    reading_timestamp,
                ),
            )


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logging.info(
            "Connected to MQTT broker at %s:%s",
            BROKER_HOST,
            BROKER_PORT,
        )
        client.subscribe(MQTT_TOPIC, qos=1)
        logging.info("Subscribed to topic: %s", MQTT_TOPIC)
    else:
        logging.error("MQTT connection failed. Reason code: %s", reason_code)


def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        insert_sensor_reading(payload)

        logging.info(
            "Inserted reading | topic=%s | sensor=%s | value=%s %s",
            message.topic,
            payload["sensor_id"],
            payload["value"],
            payload["unit"],
        )

    except (json.JSONDecodeError, KeyError, ValueError) as error:
        logging.error(
            "Invalid MQTT message on %s: %s",
            message.topic,
            error,
        )

    except psycopg.Error as error:
        logging.error("Database insert failed: %s", error)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="postgres-ingestion-subscriber",
)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    logging.info("Ingestion service started. Press Ctrl + C to stop.")
    client.loop_forever()

except KeyboardInterrupt:
    logging.info("Stopping ingestion service...")

finally:
    client.disconnect()
    logging.info("Disconnected from MQTT broker.")