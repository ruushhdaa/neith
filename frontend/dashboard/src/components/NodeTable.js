// src/components/NodeTable.js
// Table of all nodes with score bars

export default function NodeTable({ nodes }) {
  const sorted = [...nodes].sort((a, b) => b.score - a.score);

  return (
    <div className="card" style={{ height: "100%", overflow: "hidden",
                                   display: "flex", flexDirection: "column" }}>
      <div className="card-title">Node Risk Scores</div>

      <div style={{ overflowY: "auto", flex: 1 }}>
        {sorted.length === 0 ? (
          <div style={{ color: "#6b7280", fontSize: "12px" }}>
            Waiting for traffic...
          </div>
        ) : (
          sorted.map((node, i) => {
            const isSuspicious = node.status === "suspicious";
            const barColor     = isSuspicious ? "#ff3366" : "#00ff88";
            const barWidth     = `${(node.score * 100).toFixed(1)}%`;

            return (
              <div key={i} style={{ marginBottom: "12px" }} className="fade-in">
                <div style={{ display: "flex", justifyContent: "space-between",
                              marginBottom: "4px" }}>
                  <span style={{ fontSize: "12px",
                                 color: isSuspicious ? "#ff3366" : "#e0e0e0" }}>
                    <span className={`dot ${isSuspicious ? "dot-red" : "dot-green"}`} />
                    {node.id}
                  </span>
                  <span style={{ fontSize: "12px", color: barColor }}>
                    {node.score.toFixed(4)}
                  </span>
                </div>
                <div className="score-bar-wrap">
                  <div className="score-bar-fill"
                       style={{ width: barWidth, background: barColor }} />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}