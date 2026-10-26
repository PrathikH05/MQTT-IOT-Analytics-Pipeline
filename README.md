# MQTT IoT Analytics Pipeline

An end-to-end data engineering project that collects simulated sensor readings through MQTT, stores them in PostgreSQL, transforms them with dbt, and displays the results in a Streamlit dashboard.

A local Start/Stop controller automates the demo, so the pipeline can run without starting each component manually.

## How It Works

```text
Python Sensor Simulator
        ↓
MQTT Broker — Mosquitto
        ↓
Python Subscriber / Ingestion Service
        ↓
PostgreSQL
        ↓
dbt Models and Data Quality Tests
        ↓
Streamlit Dashboard
```

1. The simulator generates temperature, humidity, and vibration readings.
2. Mosquitto receives the readings through MQTT topics.
3. The subscriber listens for messages and writes them to PostgreSQL.
4. dbt creates hourly and daily summaries and runs data quality tests.
5. Streamlit displays the summaries with filters, metrics, and charts.

The controller manages these components locally through Start Demo and Stop Demo buttons.

## Features

- Three simulated sensor types: temperature, humidity, and vibration.
- MQTT-based publishing and ingestion.
- PostgreSQL storage for sensor readings.
- Incremental hourly and daily summaries built with dbt.
- Twelve data quality tests for required fields and unique identifiers.
- Interactive sensor-type and location filters.
- Reading counts, weighted averages, and latest reading timestamps.
- Hourly trends, daily averages, and minimum/maximum charts.
- Automatic dashboard refresh.
- A local controller for starting and stopping the demo.
- Separate log files for troubleshooting.

## Tech Stack

| Tool | Purpose |
|---|---|
| Python | Sensor simulation, ingestion, and automation |
| MQTT / Mosquitto | Message delivery |
| PostgreSQL | Data storage |
| dbt | Transformations and data quality tests |
| Streamlit | Dashboard |
| pandas / Plotly | Data preparation and visualization |
| Tkinter | Local Start/Stop controller |
| Docker Compose | PostgreSQL and MQTT broker containers |
| PowerShell | Manual pipeline automation |

## Project Structure

```text
├── api/                    # API component
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── dbt_project/
│   └── iot_analytics/      # dbt project, models, and tests
├── frontend/               # Separate frontend component
├── ingestion/
│   └── subscribe_to_postgres.py
├── init-db/                # Database initialization scripts
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
├── simulator/
│   ├── publish_sensors.py
│   └── test_mqtt_connection.py
├── demo_controller.py      # Start/Stop controller
├── Launch-Demo.bat         # Windows launcher
├── docker-compose.yml      # Local container setup
├── run_pipeline.ps1        # Manual dbt build script
├── .gitignore
└── README.md
```

The instructions below cover the MQTT → PostgreSQL → dbt → Streamlit workflow. The controller does not start the separate API or frontend components.

## Prerequisites

- Windows with PowerShell.
- Python with Tkinter support.
- Docker Desktop with Docker Compose.
- Docker Desktop CLI support for `docker desktop start`.
- Git.

The controller and launcher are designed for Windows. Other operating systems require changes to the launcher and process-management code.

## Initial Setup

### 1. Clone the repository

```powershell
git clone [https://github.com/PrathikH05/MQTT-IOT-Analytics-Pipeline.git](https://github.com/PrathikH05/MQTT-IOT-Analytics-Pipeline.git)
cd MQTT-IOT-Analytics-Pipeline
```

### 2. Create the Python environment

The controller expects a virtual environment named `dbt-env` in the repository root.

```powershell
python -m venv dbt-env
.\dbt-env\Scripts\Activate.ps1
```

Install the packages used by the core pipeline:

```powershell
python -m pip install paho-mqtt "psycopg[binary]" psycopg2-binary pandas plotly streamlit streamlit-autorefresh dbt-postgres
```

The ingestion service uses Psycopg 3, while the dashboard uses Psycopg 2.

### 3. Review the database configuration

Make sure the connection settings match across:

- `docker-compose.yml`
- `ingestion/subscribe_to_postgres.py`
- `dashboard/app.py`
- Your local dbt `profiles.yml`

The local demo uses:

| Component | Address |
|---|---|
| MQTT broker | `localhost:1883` |
| PostgreSQL | `localhost:5432` |
| PostgreSQL database | `iot_pipeline` |
| Dashboard | `http://localhost:8503` |

The Docker Compose service names are `mosquitto` and `postgres`.

### 4. Configure dbt

The dbt project is located at:

```text
dbt_project/iot_analytics/
```

Create or update your local dbt profile, normally located at:

```text
~/.dbt/profiles.yml
```

Use the profile name declared in the project's `dbt_project.yml`, and configure it for your local PostgreSQL database.

Local dbt profiles are excluded from version control, so cloning the repository does not configure this connection automatically.

## Run the Automated Demo

### 1. Open the controller

Double-click `Launch-Demo.bat` in the repository root.

Alternatively, run:

```powershell
.\Launch-Demo.bat
```

The controller opens with three buttons:

- `Start Demo`
- `Stop Demo`
- `Open Logs`

Keep only one controller window open. Stop any manually running simulator, subscriber, or dashboard before starting the automated demo.

### 2. Click Start Demo

The controller performs the following steps:

```text
Start Docker Desktop if needed
        ↓
Start PostgreSQL and Mosquitto
        ↓
Wait for their ports to become reachable
        ↓
Start the ingestion service
        ↓
Start the sensor simulator
        ↓
Run the initial dbt build
        ↓
Start the dashboard and open the browser
        ↓
Continue periodic dbt builds
```

When startup finishes, the controller displays:

```text
DEMO RUNNING. Browser opened.
```

Open the following address if the browser does not appear:

```text
http://localhost:8503
```

### 3. Watch the dashboard update

The simulator publishes readings continuously while the demo is running.

The controller runs dbt builds sequentially, waiting 20 seconds after each completed build before starting the next one.

The dashboard refreshes every five seconds. New summary values appear after a successful dbt build and a subsequent dashboard refresh.

This is continuous ingestion with periodic analytics updates, not an immediate dashboard update for every individual message.

### 4. Click Stop Demo

Wait until the controller displays:

```text
Controller idle.
```

During shutdown, the controller:

1. Waits for any active dbt build or Docker command to finish.
2. Stops the simulator.
3. Allows a short delay for remaining messages to be processed.
4. Stops the ingestion service and dashboard.
5. Stops the project's PostgreSQL and Mosquitto containers.

Important notes:

- Docker Desktop itself stays open.
- Database volumes are not deliberately deleted.
- The browser tab remains open, but its dashboard server stops.
- The final few readings may not reach the summary tables until the next dbt build.
- Closing the controller window requests the same shutdown.
- Avoid force-closing the controller during cleanup.
- The controller stops the project's containers even if they were running before Start Demo was clicked.

The short processing delay is a practical demo measure, not a guarantee that every pending message has been drained.

## Running the Project Manually

The manual workflow is useful for development and troubleshooting.

Do not run it alongside the automated controller.

### 1. Start Docker Desktop and the containers

From the repository root:

```powershell
docker compose up -d
docker compose ps
```

Confirm that PostgreSQL and Mosquitto are running.

### 2. Start the subscriber

In a PowerShell terminal:

```powershell
.\dbt-env\Scripts\Activate.ps1
python ingestion\subscribe_to_postgres.py
```

The subscriber listens to `sensors/#` and logs inserted readings.

### 3. Start the simulator

In another terminal, from the repository root:

```powershell
.\dbt-env\Scripts\Activate.ps1
python simulator\publish_sensors.py
```

The simulator publishes to these topics:

| Sensor | MQTT Topic | Unit |
|---|---|---|
| Temperature | `sensors/temperature` | C |
| Humidity | `sensors/humidity` | % |
| Vibration | `sensors/vibration` | mm/s |

Start the subscriber before the simulator.

To finish collection, stop the simulator with `Ctrl+C`, allow the subscriber to process remaining messages, then stop the subscriber.

### 4. Run dbt

From the repository root:

```powershell
.\run_pipeline.ps1
```

A successful run ends with:

```text
Pipeline OK
```

The script changes the terminal's current directory to the dbt project. Return to the repository root before running the next command.

### 5. Launch the dashboard

With the Python environment active, run:

```powershell
python -m streamlit run dashboard\app.py --server.port 8503
```

Open:

```text
http://localhost:8503
```

For new readings to appear in the analytics summaries, rerun dbt. Dashboard refresh alone does not run the transformation pipeline.

## Dashboard

The dashboard includes:

- Sensor-type and location filters.
- Total reading count.
- Distinct sensor count.
- An overall average weighted by reading counts.
- The latest sensor reading timestamp.
- Hourly average trends.
- Daily average charts.
- Daily minimum and maximum charts.
- An expandable hourly summary table.
- A manual Refresh data button.

### How to Read the Charts

- Readings within the same hour contribute to one hourly summary.
- The hourly chart preserves actual time gaps.
- Daily charts show recorded dates with equal spacing.
- Missing dates are not filled with synthetic readings.
- The latest reading timestamp refers to sensor data, not simply the last webpage refresh.

### Screenshots

Screenshots of the dashboard can be added here to show the filters, summary metrics, and sensor trends.

## dbt Models and Tests

| Model | Materialization | Purpose |
|---|---|---|
| `stg_iot` | View | Staging layer for sensor readings |
| `hourly_sensor_summary` | Incremental | Hourly sensor summaries |
| `daily_sensor_summary` | Incremental | Daily sensor summaries |

The project includes twelve data tests covering:

- Required reading identifiers.
- Required reading timestamps and sensor identifiers.
- Unique reading identifiers.
- Required hourly and daily summary keys.
- Unique sensor-hour and sensor-day keys.

A verified local run completed all three models and twelve tests without warnings or errors.

These tests check the configured nullability and uniqueness rules. They do not establish sensor accuracy or guarantee data freshness.

## Logs and Troubleshooting

### Controller Logs

Click `Open Logs` to view:

```text
logs/demo/
├── subscriber.log
├── simulator.log
├── dbt.log
└── dashboard.log
```

If startup fails, read the controller's error message and the relevant log file.

### Dashboard Port Already in Use

If port `8503` is occupied, stop the previous Streamlit server with `Ctrl+C` before starting the controller again.

### Docker Does Not Start

Open Docker Desktop manually and resolve any startup prompts or engine errors, then retry Start Demo.

To inspect the containers:

```powershell
docker compose ps -a
docker compose logs --tail 100
```

### Missing Python Package

Use the project's Python executable to install packages into the correct environment:

```powershell
.\dbt-env\Scripts\python.exe -m pip install PACKAGE_NAME
```

Replace `PACKAGE_NAME` with the required package.

### dbt Build Fails

Check:

- The local `profiles.yml` configuration.
- The database connection settings.
- Whether PostgreSQL is running.
- `logs/demo/dbt.log`.

### Readings Do Not Update

Check the workflow in order:

1. Confirm that the simulator is running.
2. Check the subscriber log for successful inserts.
3. Confirm that a dbt build completed successfully.
4. Wait for the next dashboard refresh.
5. Check the selected sensor type and locations.

## Security and Scope

This project is intended for local learning and demonstrations.

- Sensor readings are simulated, not collected from physical equipment.
- Local demonstration credentials must not be reused for real deployments.
- Move credentials out of source code before connecting to real infrastructure.
- Keep local `.env` files, dbt profiles, and application secrets out of version control.
- Review authentication, encryption, permissions, and network exposure before deployment.
- Removing a file in a later commit does not remove it from earlier Git history.

The controller is a local desktop tool. It does not publish the dashboard to the internet or provide a production deployment.

## Future Improvements

- Environment-based configuration.
- Pinned dependency versions.
- Data freshness checks and sensor-value validation.
- Automated ingestion tests.
- CI checks for Python and dbt.
- More graceful message-draining and process shutdown.
- Separate deployment instructions for the API and frontend.

## Author

[Prathik H](https://github.com/PrathikH05)