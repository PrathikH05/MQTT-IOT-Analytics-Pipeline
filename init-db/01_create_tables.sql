CREATE TABLE IF NOT EXISTS raw_sensor_data (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    value NUMERIC(10,2) NOT NULL,
    unit VARCHAR(20),
    location VARCHAR(50),
    reading_timestamp TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensor_type
ON raw_sensor_data(sensor_type);

CREATE INDEX IF NOT EXISTS idx_reading_timestamp
ON raw_sensor_data(reading_timestamp);