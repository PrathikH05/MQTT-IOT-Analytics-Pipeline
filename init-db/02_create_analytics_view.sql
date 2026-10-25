CREATE OR REPLACE VIEW sensor_reading_status AS
SELECT
    id,
    sensor_id,
    sensor_type,
    value,
    unit,
    location,
    reading_timestamp,
    ingested_at,
    CASE
        WHEN sensor_type = 'temperature' AND value > 65 THEN 'anomaly'
        WHEN sensor_type = 'humidity' AND value > 85 THEN 'anomaly'
        WHEN sensor_type = 'vibration' AND value > 7 THEN 'anomaly'
        ELSE 'normal'
    END AS status
FROM raw_sensor_data;