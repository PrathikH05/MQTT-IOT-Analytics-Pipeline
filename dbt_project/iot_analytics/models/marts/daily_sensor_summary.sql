{{
  config(
    materialized = 'incremental',
    unique_key = 'sensor_day_key',
    incremental_strategy = 'merge'
  )
}}

with staged as (
    select *
    from {{ ref('stg_iot') }}
    {% if is_incremental() %}
    where reading_timestamp >= (
        select coalesce(max(reading_date), '1900-01-01'::date)
        from {{ this }}
    )
    {% endif %}
),

daily_summary as (
    select
        sensor_id,
        sensor_type,
        location,
        date_trunc('day', reading_timestamp)::date as reading_date,
        count(*) as readings_count,
        avg(value) as avg_value,
        min(value) as min_value,
        max(value) as max_value,
        min(reading_timestamp) as first_reading_at,
        max(reading_timestamp) as last_reading_at,
        sensor_id || '-' || (date_trunc('day', reading_timestamp)::date)::text as sensor_day_key
    from staged
    group by
        sensor_id,
        sensor_type,
        location,
        date_trunc('day', reading_timestamp)
)

select * from daily_summary