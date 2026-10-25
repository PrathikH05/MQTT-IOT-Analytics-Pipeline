# MQTT IoT Data Pipeline

End-to-end IoT analytics pipeline: sensor data is published over MQTT, stored in PostgreSQL, transformed with dbt, and visualised in a Streamlit dashboard.

## Architecture

```text
Sensors (Python) -> MQTT (Mosquitto) -> PostgreSQL (raw)
    -> dbt: stg_iot -> hourly_sensor_summary / daily_sensor_summary
    -> Streamlit dashboard
```

## Tech stack

Python 3.12, MQTT (Eclipse Mosquitto), PostgreSQL 16, dbt Core, Streamlit, Plotly, Docker, PowerShell

## Data models

| Model | Type | Purpose |
|---|---|---|
| `public.raw_sensor_data` | table | Raw readings from the ingestion script |
| `stg_iot` | view | Cleaned, tested staging layer |
| `hourly_sensor_summary` | incremental | Count, avg, min, max per sensor per hour |
| `daily_sensor_summary` | incremental | Count, avg, min, max per sensor per day |

12 dbt tests cover not-null and unique constraints on key columns.

## How to run

1. Start services: `docker start iot-postgres mqtt-broker`
2. Run the ingestion/simulator scripts to produce data.
3. Build models and run tests: `.\run_pipeline.ps1`
4. Start the dashboard: `streamlit run dashboard\app.py`

## Design notes

- Incremental models reprocess the latest period on each run, so late readings are included and `merge` prevents duplicates.
- Credentials in the dashboard are for local development only.