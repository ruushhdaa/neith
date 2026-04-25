// src/components/StatusBar.js
// Top bar — model status, window count, node count, last updated

export default function StatusBar({ status, error }) {
  return (
    <div style={{
      background:     "#0f1629",
      borderBottom:   "1px solid #1e3a5f",
      padding:        "12px 24px",
      display:        "flex",
      alignItems:     "center",
      justifyContent: "space-between",
      flexWrap:       "wrap",
      gap:            "12px",
    }}>

      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span style={{ color: "#00d4ff", fontSize: "18px", fontWeight: "bold",
                       letterSpacing: "3px" }}>
          NEITH
        </span>
        <span style={{ color: "#6b7280", fontSize: "11px", letterSpacing: "1px" }}>
          Network Entity Intelligence & Threat Hunter
        </span>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", gap: "24px", alignItems: "center" }}>

        {/* Model Status */}
        <div style={{ fontSize: "12px" }}>
          <span className={`dot ${status.status === "active" ? "dot-green" : "dot-yellow"}`} />
          {status.status === "active" ? "ACTIVE" : "LOADING"}
        </div>

        {/* Window */}
        <div style={{ fontSize: "12px", color: "#6b7280" }}>
          WINDOW&nbsp;
          <span style={{ color: "#e0e0e0" }}>#{status.window}</span>
        </div>

        {/* Nodes */}
        <div style={{ fontSize: "12px", color: "#6b7280" }}>
          NODES&nbsp;
          <span style={{ color: "#00d4ff" }}>{status.node_count}</span>
        </div>

        {/* Alerts */}
        <div style={{ fontSize: "12px", color: "#6b7280" }}>
          ALERTS&nbsp;
          <span style={{
            color: status.alert_count > 0 ? "#ff3366" : "#e0e0e0",
            fontWeight: status.alert_count > 0 ? "bold" : "normal",
          }}>
            {status.alert_count}
          </span>
        </div>

        {/* Last Updated */}
        <div style={{ fontSize: "11px", color: "#6b7280" }}>
          {status.last_updated ? `UPDATED ${status.last_updated}` : "WAITING..."}
        </div>

      </div>

      {/* Error */}
      {error && (
        <div style={{ color: "#ff3366", fontSize: "11px", width: "100%" }}>
          ⚠ {error}
        </div>
      )}

    </div>
  );
}