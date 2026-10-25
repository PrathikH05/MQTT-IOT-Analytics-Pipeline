from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "iot_pipeline",
    "user": "iot_user",
    "password": "iot_pass",
}

ALLOWED_SENSOR_TYPES = {"temperature", "humidity", "vibration"}


@contextmanager
def get_connection():
    connection = psycopg.connect(**DB_CONFIG)
    try:
        yield connection
    finally:
        connection.close()


def serialize_row(row: dict) -> dict:
    serialized = {}

    for key, value in row.items():
        if isinstance(value, (datetime, Decimal)):
            serialized[key] = str(value)
        else:
            serialized[key] = value

    return serialized


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


class ReadingResponse(BaseModel):
    id: int
    sensor_id: str
    sensor_type: str
    value: float
    unit: str | None
    location: str | None
    reading_timestamp: datetime
    ingested_at: datetime
    status: Literal["normal", "anomaly"]


class SummaryResponse(BaseModel):
    sensor_type: str
    total_readings: int
    anomaly_count: int
    average_value: float
    min_value: float
    max_value: float
    latest_reading_at: datetime | None


app = FastAPI(
    title="Industrial IoT Monitoring API",
    description=(
        "REST API for simulated industrial telemetry: "
        "temperature, humidity, and vibration readings."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Industrial IoT Monitoring API is running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(),
        }

    except psycopg.Error as error:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {error}",
        ) from error


@app.get("/readings", response_model=list[ReadingResponse], tags=["Readings"])
def get_recent_readings(
    limit: int = Query(default=50, ge=1, le=500),
    sensor_type: str | None = Query(default=None),
):
    if sensor_type is not None and sensor_type not in ALLOWED_SENSOR_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid sensor_type. Use temperature, humidity, "
                "or vibration."
            ),
        )

    query = """
        SELECT
            id,
            sensor_id,
            sensor_type,
            value,
            unit,
            location,
            reading_timestamp,
            ingested_at,
            status
        FROM sensor_reading_status
    """
    parameters = []

    if sensor_type is not None:
        query += " WHERE sensor_type = %s"
        parameters.append(sensor_type)

    query += " ORDER BY id DESC LIMIT %s"
    parameters.append(limit)

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query, parameters)
                readings = cursor.fetchall()

        return [serialize_row(reading) for reading in readings]

    except psycopg.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch readings: {error}",
        ) from error


@app.get(
    "/anomalies",
    response_model=list[ReadingResponse],
    tags=["Readings"],
)
def get_anomalies(
    limit: int = Query(default=50, ge=1, le=500),
):
    query = """
        SELECT
            id,
            sensor_id,
            sensor_type,
            value,
            unit,
            location,
            reading_timestamp,
            ingested_at,
            status
        FROM sensor_reading_status
        WHERE status = 'anomaly'
        ORDER BY id DESC
        LIMIT %s
    """

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query, (limit,))
                anomalies = cursor.fetchall()

        return [serialize_row(anomaly) for anomaly in anomalies]

    except psycopg.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch anomalies: {error}",
        ) from error


@app.get(
    "/summary",
    response_model=list[SummaryResponse],
    tags=["Analytics"],
)
def get_sensor_summary():
    query = """
        SELECT
            sensor_type,
            COUNT(*) AS total_readings,
            COUNT(*) FILTER (WHERE status = 'anomaly') AS anomaly_count,
            ROUND(AVG(value), 2) AS average_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value,
            MAX(reading_timestamp) AS latest_reading_at
        FROM sensor_reading_status
        GROUP BY sensor_type
        ORDER BY sensor_type
    """

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query)
                summary = cursor.fetchall()

        return [serialize_row(item) for item in summary]

    except psycopg.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not calculate summary: {error}",
        ) from error


@app.get(
    "/sensors/{sensor_type}",
    response_model=list[ReadingResponse],
    tags=["Readings"],
)
def get_sensor_history(
    sensor_type: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    if sensor_type not in ALLOWED_SENSOR_TYPES:
        raise HTTPException(
            status_code=404,
            detail="Sensor type not found.",
        )

    query = """
        SELECT
            id,
            sensor_id,
            sensor_type,
            value,
            unit,
            location,
            reading_timestamp,
            ingested_at,
            status
        FROM sensor_reading_status
        WHERE sensor_type = %s
        ORDER BY id DESC
        LIMIT %s
    """

    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                cursor.execute(query, (sensor_type, limit))
                readings = cursor.fetchall()

        return [serialize_row(reading) for reading in readings]

    except psycopg.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch sensor history: {error}",
        ) from error