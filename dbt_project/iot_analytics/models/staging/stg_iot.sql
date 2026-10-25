with raw as (
    select *
    from {{ source('raw', 'raw_sensor_data') }}
),

staged as (
    select
        id,
        sensor_id,
        sensor_type,
        value,
        unit,
        location,
        reading_timestamp,
        ingested_at
    from raw
)

select *
from staged