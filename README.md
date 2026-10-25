# MQTT IoT Analytics Pipeline

A hands-on data engineering project that collects simulated sensor readings through MQTT, stores them in PostgreSQL, transforms them with dbt, and displays the results in a Streamlit dashboard.

The project brings together streaming data ingestion and batch analytics in one local workflow.

## How It Works

```text
Python Sensor Simulator
        ↓
MQTT Broker (Mosquitto)
        ↓
Python Subscriber
        ↓
PostgreSQL
        ↓
dbt Models and Tests
        ↓
Streamlit Dashboard
```

1. The simulator generates temperature, humidity, and vibration readings.
2. Mosquitto receives the readings through MQTT topics.
3. The subscriber listens for messages and inserts them into PostgreSQL.
4. dbt creates hourly and daily summaries and runs data quality tests.
5. Streamlit displays the summaries with filters, metrics, and charts.

## Features

- Three simulated sensor types: temperature, humidity, and vibration.
- MQTT-based publishing and ingestion.
- PostgreSQL storage for sensor readings.
- Incremental hourly and daily summaries built with dbt.
- Twelve data quality tests for required fields and unique identifiers.
- A dashboard with sensor-type and location filters.
- Reading counts, weighted averages, and latest reading timestamps.
- Hourly trends, daily averages, and daily minimum/maximum charts.

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Sensor simulation and data ingestion |
| MQTT / Mosquitto | Message delivery |
| PostgreSQL | Data storage |
| dbt | Transformations and data quality tests |
| Streamlit | Dashboard |
| pandas / Plotly | Data preparation and charts |
| Docker Compose | Local infrastructure |
| PowerShell | Pipeline automation |

## Project Structure

```text
├── simulator/          # Generates and publishes sensor readings
├── ingestion/          # Subscribes to MQTT and writes to PostgreSQL
├── init-db/            # Database initialization scripts
├── mosquitto/          # MQTT broker configuration
├── dbt_project/        # dbt models and tests
├── dashboard/          # Streamlit dashboard
├── api/                # API component
├── frontend/           # Separate frontend component
├── docker-compose.yml  # Local container setup
└── run_pipeline.ps1    # Runs the dbt pipeline
```

The instructions below cover the MQTT, PostgreSQL, dbt, and Streamlit workflow. The repository also includes separate API and frontend components.

## Getting Started

### Prerequisites

- Python
- Docker Desktop with Docker Compose
- Git
- PowerShell

The commands below are for Windows PowerShell.

### 1. Clone the repository

```powershell
git clone [https://github.com/PrathikH05/MQTT-IOT-Analytics-Pipeline.git](https://github.com/PrathikH05/MQTT-IOT-Analytics-Pipeline.git)
cd MQTT-IOT-Analytics-Pipeline
```

### 2. Set up the Python environment

```powershell
python -m venv dbt-env
.\dbt-env\Scripts\Activate.ps1
```

Install the packages used by the core pipeline:

```powershell
python -m pip install paho-mqtt "psycopg[binary]" psycopg2-binary pandas plotly streamlit dbt-postgres
```

### 3. Check the configuration

Before starting, make sure the database settings match across:

- `docker-compose.yml`
- `ingestion/subscribe_to_postgres.py`
- `dashboard/app.py`
- Your local dbt `profiles.yml`

Configure the dbt profile using the profile name in the project's `dbt_project.yml`. The local `profiles.yml` file is not included in version control.

The local demo uses MQTT at `localhost:1883` and a PostgreSQL database named `iot_pipeline`.

### 4. Start the containers

From the repository root:

```powershell
docker compose up -d
docker compose ps
```

Confirm that PostgreSQL and Mosquitto are running.

## Running the Project

Use separate PowerShell terminals for the subscriber and simulator. In each terminal, open the repository folder and activate the Python environment.

### 1. Start the subscriber

```powershell
.\dbt-env\Scripts\Activate.ps1
python ingestion\subscribe_to_postgres.py
```

The subscriber listens to `sensors/#` and logs each inserted reading.

### 2. Start the simulator

In a second terminal:

```powershell
.\dbt-env\Scripts\Activate.ps1
python simulator\publish_sensors.py
```

The simulator publishes readings to these topics:

| Sensor | MQTT Topic | Unit |
|---|---|---|
| Temperature | `sensors/temperature` | C |
| Humidity | `sensors/humidity` | % |
| Vibration | `sensors/vibration` | mm/s |

Leave both scripts running to collect data.

When finished, stop the simulator with `Ctrl+C`, let the subscriber process any remaining messages, then stop the subscriber.

### 3. Run the dbt pipeline

From the repository root, with the Python environment active:

```powershell
.\run_pipeline.ps1
```

A successful run ends with:

```text
Pipeline OK
```

The verified run completed all three models and twelve data tests without warnings or errors.

### 4. Start the dashboard

Return to the repository root if the pipeline script changed your current directory, then run:

```powershell
streamlit run dashboard\app.py --server.port 8503
```

Open `http://localhost:8503` in your browser.

## Dashboard

The dashboard includes:

- Sensor-type and location filters.
- Total readings and sensor count.
- An overall average weighted by reading counts.
- The latest reading timestamp.
- Hourly average trends.
- Daily average and minimum/maximum charts.
- An expandable hourly summary table.

After collecting new readings, run the dbt pipeline again and click `Refresh data` in the dashboard.

The dashboard reads summary tables; refreshing it does not run dbt automatically.

### Screenshots

Dashboard screenshots can be added here to show the filters, charts, and latest readings.

## dbt Models and Tests

| Model | Description |
|---|---|
| `stg_iot` | Staging view for sensor readings |
| `hourly_sensor_summary` | Incremental hourly summaries |
| `daily_sensor_summary` | Incremental daily summaries |

The twelve tests check required fields and unique identifiers across these models.

These tests help catch missing values and duplicate keys. They do not verify that simulated sensor values represent real equipment behavior.

## A Few Things to Know

- Sensor readings are simulated, not collected from physical devices.
- Readings collected within the same hour appear in one hourly summary.
- The hourly chart preserves actual time gaps.
- Daily charts show recorded dates with equal spacing.
- Docker containers must remain running while the pipeline accesses MQTT or PostgreSQL.
- Local database credentials are for demonstration only. Do not reuse them for real deployments.
- Local environments, dependencies, and broker runtime files are excluded through `.gitignore`.

## Future Improvements

- Move database credentials out of source code.
- Pin dependency versions for easier setup.
- Schedule dbt runs automatically.
- Add data freshness checks and sensor-value validation.
- Add automated ingestion tests and CI checks.

## Author

[Prathik H](https://github.com/PrathikH05)