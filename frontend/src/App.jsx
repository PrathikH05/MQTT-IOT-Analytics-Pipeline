import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const sensorLabels = {
  temperature: "Temperature",
  humidity: "Humidity",
  vibration: "Vibration",
};

const sensorIcons = {
  temperature: "🌡️",
  humidity: "💧",
  vibration: "📳",
};

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function formatTime(timestamp) {
  if (!timestamp) return "No data";

  return new Date(timestamp).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

function Dashboard() {
  const [summary, setSummary] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [readings, setReadings] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState("");

  async function loadDashboardData() {
    try {
      const [summaryResponse, anomaliesResponse, readingsResponse] =
        await Promise.all([
          fetch(`${API_BASE_URL}/summary`),
          fetch(`${API_BASE_URL}/anomalies?limit=8`),
          fetch(`${API_BASE_URL}/readings?limit=12`),
        ]);

      if (
        !summaryResponse.ok ||
        !anomaliesResponse.ok ||
        !readingsResponse.ok
      ) {
        throw new Error("Could not load dashboard data from the API.");
      }

      const [summaryData, anomaliesData, readingsData] = await Promise.all([
        summaryResponse.json(),
        anomaliesResponse.json(),
        readingsResponse.json(),
      ]);

      setSummary(summaryData);
      setAnomalies(anomaliesData);
      setReadings(readingsData);
      setLastUpdated(new Date());
      setError("");
    } catch (requestError) {
      setError(
        "Cannot connect to FastAPI. Make sure the backend is running on port 8000."
      );
      console.error(requestError);
    }
  }

  useEffect(() => {
    loadDashboardData();

    const refreshTimer = setInterval(loadDashboardData, 5000);

    return () => clearInterval(refreshTimer);
  }, []);

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">REAL-TIME INDUSTRIAL IOT PLATFORM</p>
          <h1>Sensor Health Monitor</h1>
          <p className="subtitle">
            MQTT telemetry, PostgreSQL analytics, and live anomaly tracking
          </p>
        </div>

        <div className="live-status">
          <span className="live-dot" />
          <span>LIVE</span>
          <small>
            Updated: {lastUpdated ? formatTime(lastUpdated) : "Loading..."}
          </small>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="metrics-grid">
        {summary.map((item) => (
          <article className="metric-card" key={item.sensor_type}>
            <div className="metric-top">
              <span className="sensor-icon">
                {sensorIcons[item.sensor_type]}
              </span>
              <span
                className={
                  item.anomaly_count > 0
                    ? "anomaly-badge"
                    : "normal-badge"
                }
              >
                {item.anomaly_count > 0
                  ? `${item.anomaly_count} Alert${
                      item.anomaly_count > 1 ? "s" : ""
                    }`
                  : "Normal"}
              </span>
            </div>

            <p className="sensor-name">
              {sensorLabels[item.sensor_type] ?? item.sensor_type}
            </p>
            <p className="metric-value">
              {formatNumber(item.average_value)}
            </p>
            <p className="metric-unit">
              Average {item.sensor_type} value
            </p>

            <div className="metric-footer">
              <span>Min: {formatNumber(item.min_value)}</span>
              <span>Max: {formatNumber(item.max_value)}</span>
              <span>{item.total_readings} readings</span>
            </div>
          </article>
        ))}
      </section>

      <section className="content-grid">
        <article className="panel anomalies-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">ATTENTION REQUIRED</p>
              <h2>Recent Anomalies</h2>
            </div>
            <span className="counter">{anomalies.length}</span>
          </div>

          {anomalies.length === 0 ? (
            <p className="empty-state">No anomalies detected yet.</p>
          ) : (
            <div className="anomaly-list">
              {anomalies.map((reading) => (
                <div className="anomaly-item" key={reading.id}>
                  <div>
                    <p className="anomaly-title">
                      {sensorLabels[reading.sensor_type]} —{" "}
                      {formatNumber(reading.value)} {reading.unit}
                    </p>
                    <p className="anomaly-details">
                      {reading.sensor_id} · {reading.location} ·{" "}
                      {formatTime(reading.reading_timestamp)}
                    </p>
                  </div>
                  <span className="danger-label">ANOMALY</span>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="panel readings-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">MQTT TELEMETRY</p>
              <h2>Latest Readings</h2>
            </div>
            <button className="refresh-button" onClick={loadDashboardData}>
              Refresh
            </button>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Sensor</th>
                  <th>Value</th>
                  <th>Location</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {readings.map((reading) => (
                  <tr key={reading.id}>
                    <td>
                      <strong>
                        {sensorLabels[reading.sensor_type] ??
                          reading.sensor_type}
                      </strong>
                      <small>{reading.sensor_id}</small>
                    </td>
                    <td>
                      {formatNumber(reading.value)} {reading.unit}
                    </td>
                    <td>{reading.location}</td>
                    <td>
                      <span
                        className={
                          reading.status === "anomaly"
                            ? "table-status anomaly"
                            : "table-status normal"
                        }
                      >
                        {reading.status}
                      </span>
                    </td>
                    <td>{formatTime(reading.reading_timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </main>
  );
}

export default Dashboard;