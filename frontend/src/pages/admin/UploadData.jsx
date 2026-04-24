import { useState } from "react";

import api from "../../api/axios";

export default function UploadData() {
  const [file, setFile] = useState(null);
  const [minSupport, setMinSupport] = useState(0.02);
  const [minConfidence, setMinConfidence] = useState(0.3);
  const [status, setStatus] = useState({ loading: false, message: "", rules: 0 });

  const processAndTrain = async () => {
    if (!file) {
      setStatus({ loading: false, message: "Select a CSV file first", rules: 0 });
      return;
    }

    setStatus({ loading: true, message: "Uploading and training...", rules: 0 });

    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post("/api/admin/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const trainRes = await api.post("/api/admin/train", {
        min_support: minSupport,
        min_confidence: minConfidence,
      });

      setStatus({
        loading: false,
        message: "Training complete",
        rules: trainRes.data.rules_generated || 0,
      });
    } catch (error) {
      setStatus({
        loading: false,
        message: error.response?.data?.error || "Upload/train failed",
        rules: 0,
      });
    }
  };

  return (
    <section className="panel admin-section">
      <h2>Upload and Train</h2>
      <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} className="file-input" />

      <label>
        Min support: {minSupport.toFixed(2)}
        <input
          type="range"
          min="0.01"
          max="0.1"
          step="0.01"
          value={minSupport}
          onChange={(e) => setMinSupport(Number(e.target.value))}
        />
      </label>

      <label>
        Min confidence: {minConfidence.toFixed(2)}
        <input
          type="range"
          min="0.1"
          max="0.9"
          step="0.05"
          value={minConfidence}
          onChange={(e) => setMinConfidence(Number(e.target.value))}
        />
      </label>

      <button className="primary-btn" type="button" onClick={processAndTrain} disabled={status.loading}>
        {status.loading ? "Processing..." : "Process & Train"}
      </button>

      {status.message && <p className="status-line">{status.message}</p>}
      {status.rules > 0 && <p className="status-line">{status.rules} rules generated.</p>}
    </section>
  );
}
