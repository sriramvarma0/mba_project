import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const efficiencyData = [
  { name: "Traditional System", value: 58.23 },
  { name: "Apriori", value: 72.45 },
  { name: "FP-Growth/Proposed", value: 89.67 },
];

const responseData = [
  { name: "Single Item Query", value: 387 },
  { name: "Multi Item Query", value: 824 },
  { name: "Batch Processing", value: 1396 },
];

export default function Reports() {
  return (
    <section className="admin-section">
      <h2 className="section-title">Reports and Analytics</h2>
      <div className="panel">
        <h3>Recommendation Efficiency (Figure 6.1)</h3>
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={efficiencyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#2c7f5e" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel">
        <h3>API Response Time in ms (Figure 6.2)</h3>
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={responseData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#1d5f92" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <p>
        The FP-Growth based recommendation pipeline shows substantially higher efficiency than both a traditional baseline and
        Apriori, while preserving sub-1.5s response time even for batch recommendation calls.
      </p>
    </section>
  );
}
