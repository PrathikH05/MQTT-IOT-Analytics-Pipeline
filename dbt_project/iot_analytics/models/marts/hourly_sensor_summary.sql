{{
  config(
    materialized = 'incremental',
    unique_key = 'sensor_hour_key',
    incremental_strategy = 'merge'
  )
}}

with staged as (
    select *
    from {{ ref('stg_iot') }}
    {% if is_incremental() %}
    where reading_timestamp >= (
        select coalesce(max(reading_hour), '1900-01-01'::timestamp)
        from {{ this }}
    )
    {% endif %}
),

hourly_summary as (
    select
        sensor_id,
        sensor_type,
        location,
        date_trunc('hour', reading_timestamp) as reading_hour,
        count(*) as readings_count,
        avg(value) as avg_value,
        min(value) as min_value,
        max(value) as max_value,
        min(reading_timestamp) as first_reading_at,
        max(reading_timestamp) as last_reading_at,
        sensor_id || '-' || (date_trunc('hour', reading_timestamp))::text as sensor_hour_key
    from staged
    group by
        sensor_id,
        sensor_type,
        location,
        date_trunc('hour', reading_timestamp)
)

select * from hourly_summary