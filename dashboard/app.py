import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st


st.set_page_config(
    page_title="IoT Sensor Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_data(query):
    conn = psycopg2.connect(
        host="localhost",
        dbname="iot_pipeline",
        user="iot_user",
        password="iot_pass",
    )
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


st.title("📊 IoT Sensor Analytics Dashboard")
st.caption(
    "MQTT → PostgreSQL → dbt (staging + incremental marts) → Streamlit"
)

st.sidebar.header("Filters")

if st.sidebar.button("Refresh data"):
    load_data.clear()

try:
    hourly = load_data(
        """
        SELECT *
        FROM analytics.hourly_sensor_summary
        ORDER BY reading_hour, sensor_id
        """
    )
    daily = load_data(
        """
        SELECT *
        FROM analytics.daily_sensor_summary
        ORDER BY reading_date, sensor_id
        """
    )
except Exception as exc:
    st.error(
        "Could not load dashboard data. Check that PostgreSQL is running "
        "and the dbt summary models exist."
    )
    with st.expander("Error details"):
        st.code(str(exc))
    st.stop()


if hourly.empty:
    st.warning("No hourly summary data is available. Run the pipeline first.")
    st.stop()


# Prepare timestamp and numeric columns.
for column in ["reading_hour", "first_reading_at", "last_reading_at"]:
    if column in hourly.columns:
        hourly[column] = pd.to_datetime(hourly[column], errors="coerce")

daily["reading_date"] = pd.to_datetime(
    daily["reading_date"], errors="coerce"
)

for frame in [hourly, daily]:
    for column in [
        "readings_count",
        "avg_value",
        "min_value",
        "max_value",
    ]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")


# Sidebar filters.
sensor_types = sorted(
    hourly["sensor_type"].dropna().unique().tolist()
)

if not sensor_types:
    st.warning("No sensor types are available.")
    st.stop()

sensor_type = st.sidebar.selectbox("Sensor type", sensor_types)

locations = sorted(
    hourly.loc[
        hourly["sensor_type"] == sensor_type, "location"
    ].dropna().unique().tolist()
)

chosen_locations = st.sidebar.multiselect(
    "Location",
    options=locations,
    default=locations,
)

h = hourly.loc[
    (hourly["sensor_type"] == sensor_type)
    & hourly["location"].isin(chosen_locations)
].copy()

d = daily.loc[
    (daily["sensor_type"] == sensor_type)
    & daily["location"].isin(chosen_locations)
].copy()

if h.empty:
    st.warning("No data for this selection. Select at least one location.")
    st.stop()

h = h.sort_values(["reading_hour", "sensor_id"])


# Summary metrics: weight hourly averages by their reading counts.
total_readings = int(h["readings_count"].sum())
sensor_count = h["sensor_id"].nunique()

valid_average_rows = (
    h["avg_value"].notna()
    & h["readings_count"].notna()
    & (h["readings_count"] > 0)
)
average_rows = h.loc[valid_average_rows]
average_count = average_rows["readings_count"].sum()

overall_average = (
    (
        average_rows["avg_value"]
        * average_rows["readings_count"]
    ).sum()
    / average_count
    if average_count > 0
    else None
)

latest_reading = h["last_reading_at"].max()
latest_label = (
    latest_reading.strftime("%Y-%m-%d %H:%M")
    if pd.notna(latest_reading)
    else "N/A"
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total readings", f"{total_readings:,}")
c2.metric("Sensors", sensor_count)
c3.metric(
    f"Overall avg ({sensor_type})",
    f"{overall_average:.2f}" if overall_average is not None else "N/A",
)
c4.metric("Latest reading", latest_label)


# Keep the hourly axis as a real timeline.
st.subheader(f"Hourly average – {sensor_type}")

hourly_fig = px.line(
    h,
    x="reading_hour",
    y="avg_value",
    color="sensor_id",
    markers=True,
    labels={
        "reading_hour": "Hour",
        "avg_value": "Average value",
        "sensor_id": "Sensor",
    },
)

st.plotly_chart(hourly_fig, use_container_width=True)


# Use categorical dates for the daily charts.
if d.empty:
    st.info("No daily summary data is available for this selection.")
else:
    d = d.dropna(subset=["reading_date"])
    d = d.sort_values(["reading_date", "sensor_id"])
    d["reading_date"] = d["reading_date"].dt.strftime("%Y-%m-%d")
    date_order = sorted(d["reading_date"].unique().tolist())

    left, right = st.columns(2)

    with left:
        st.subheader("Daily average")

        daily_fig = px.bar(
            d,
            x="reading_date",
            y="avg_value",
            color="sensor_id",
            barmode="group",
            labels={
                "reading_date": "Date",
                "avg_value": "Average value",
                "sensor_id": "Sensor",
            },
        )

        daily_fig.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=date_order,
        )

        st.plotly_chart(daily_fig, use_container_width=True)

    with right:
        st.subheader("Daily min / max range")

        ranges = d.melt(
            id_vars=["reading_date", "sensor_id"],
            value_vars=["min_value", "max_value"],
            var_name="statistic",
            value_name="value",
        )

        ranges["statistic"] = ranges["statistic"].map(
            {
                "min_value": "Minimum",
                "max_value": "Maximum",
            }
        )

        range_fig = px.line(
            ranges,
            x="reading_date",
            y="value",
            color="sensor_id",
            line_dash="statistic",
            markers=True,
            labels={
                "reading_date": "Date",
                "value": "Value",
                "sensor_id": "Sensor",
                "statistic": "Statistic",
            },
        )

        range_fig.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=date_order,
        )

        st.plotly_chart(range_fig, use_container_width=True)

    st.caption(
        "Daily charts show recorded dates with equal spacing; "
        "gaps between dates are not drawn to scale."
    )


with st.expander("View hourly summary table"):
    st.dataframe(
        h.drop(columns=["sensor_hour_key"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
    )