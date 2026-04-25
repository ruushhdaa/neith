// src/components/AlertFeed.js
// Live scrolling alert feed

export default function AlertFeed({ alerts }) {
  return (
    <div className="card" style={{ height: "100%", overflow: "hidden",
                                   display: "flex", flexDirection: "column" }}>
      <div className="card-title">⚠ Alert Feed</div>

      <div style={{ overflowY: "auto", flex: 1 }}>
        {alerts.length === 0 ? (
          <div style={{ color: "#6b7280", fontSize: "12px", padding: "8px 0" }}>
            <span className="dot dot-green" />
            No alerts. Network appears normal.
          </div>
        ) : (
          alerts.map((alert, i) => (
            <div
              key={i}
              className="fade-in"
              style={{
                borderLeft:   "2px solid #ff3366",
                paddingLeft:  "10px",
                marginBottom: "10px",
                background:   "#1a0a0f",
                borderRadius: "0 4px 4px 0",
                padding:      "8px 10px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between",
                            alignItems: "center" }}>
                <span style={{ color: "#ff3366", fontSize: "13px",
                               fontWeight: "bold" }}>
                  {alert.ip}
                </span>
                <span style={{ color: "#6b7280", fontSize: "10px" }}>
                  {alert.timestamp}
                </span>
              </div>
              <div style={{ marginTop: "4px", display: "flex",
                            alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "11px", color: "#6b7280" }}>
                  Score:
                </span>
                <span style={{ fontSize: "12px", color: "#ffd700" }}>
                  {alert.score.toFixed(4)}
                </span>
                <span style={{ fontSize: "10px", color: "#ff3366" }}>
                  SUSPICIOUS
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}