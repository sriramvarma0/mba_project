import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import api from "../../api/axios";

function formatToIST(value) {
  if (!value) {
    return "N/A";
  }

  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(value);
  const normalized = hasTimezone ? value : `${value}Z`;
  const date = new Date(normalized);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const formatted = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  }).format(date);

  return `${formatted} IST`;
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [trainStatus, setTrainStatus] = useState("");

  const fetchStats = async () => {
    const { data } = await api.get("/api/admin/stats");
    setStats(data);
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const retrain = async () => {
    try {
      setTrainStatus("Retraining...");
      await api.post("/api/admin/train", {});
      setTrainStatus("Retraining complete.");
      await fetchStats();
    } catch (error) {
      setTrainStatus(error.response?.data?.error || "Retraining failed.");
    }
  };

  if (!stats) {
    return <p>Loading dashboard...</p>;
  }

  const chartData = (stats.product_frequencies || []).slice(0, 10);

  return (
    <section className="admin-section">
      <h2 className="section-title">Admin Dashboard</h2>
      <div className="admin-actions">
        <button className="primary-btn" type="button" onClick={retrain}>
          Retrain Model
        </button>
        {trainStatus && <p className="status-line">{trainStatus}</p>}
      </div>
      <div className="stats-grid">
        <div className="stat-card">
          <span>Total Transactions</span>
          <strong>{stats.total_transactions}</strong>
        </div>
        <div className="stat-card">
          <span>Total Rules Generated</span>
          <strong>{stats.total_rules}</strong>
        </div>
        <div className="stat-card">
          <span>Top Product</span>
          <strong>{stats.top_product?.name || "N/A"}</strong>
        </div>
        <div className="stat-card">
          <span>Last Training Time</span>
          <strong>{formatToIST(stats.last_training_time)}</strong>
        </div>
      </div>

      <div className="panel">
        <h3>Top 10 Products by Frequency</h3>
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="frequency" fill="#ef6c3f" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
