import { useEffect, useMemo, useState } from "react";

import api from "../../api/axios";

export default function RulesManager() {
  const [rules, setRules] = useState([]);
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const loadRules = async () => {
    const { data } = await api.get("/api/admin/rules");
    setRules(data);
  };

  useEffect(() => {
    loadRules();
  }, []);

  const filtered = useMemo(() => {
    const normalizedSearch = searchText.trim().toLowerCase();

    return rules.filter((rule) => {
      const statusMatches =
        statusFilter === "all" ||
        (statusFilter === "active" && rule.is_active) ||
        (statusFilter === "inactive" && !rule.is_active);

      if (!statusMatches) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      const antecedentsText = rule.antecedents.join(" ").toLowerCase();
      const consequentsText = rule.consequents.join(" ").toLowerCase();
      return (
        antecedentsText.includes(normalizedSearch) ||
        consequentsText.includes(normalizedSearch)
      );
    });
  }, [rules, searchText, statusFilter]);

  const toggleRule = async (ruleId, isActive) => {
    await api.patch(`/api/admin/rules/${ruleId}`, { is_active: !isActive });
    await loadRules();
  };

  return (
    <section className="admin-section">
      <h2 className="section-title">Rules Manager</h2>
      <div className="filters">
        <label>
          Search Rule
          <input
            type="text"
            placeholder="Type product/sku"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </label>
        <label>
          Status
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </label>
      </div>
      <div className="panel">
        <table className="rules-table">
          <thead>
            <tr>
              <th>Antecedents</th>
              <th>Consequents</th>
              <th>Support</th>
              <th>Confidence</th>
              <th>Lift</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((rule) => (
              <tr key={rule.id}>
                <td>{rule.antecedents.join(", ")}</td>
                <td>{rule.consequents.join(", ")}</td>
                <td>{rule.support.toFixed(4)}</td>
                <td>{(rule.confidence * 100).toFixed(2)}%</td>
                <td>{rule.lift.toFixed(2)}</td>
                <td>
                  <button className="table-btn" type="button" onClick={() => toggleRule(rule.id, rule.is_active)}>
                    {rule.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
            {!filtered.length && (
              <tr>
                <td colSpan="6">No rules match the selected filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
