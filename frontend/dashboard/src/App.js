// src/App.js
// NEITH — Main Layout

import StatusBar    from "./components/StatusBar";
import NetworkGraph from "./components/NetworkGraph";
import AlertFeed   from "./components/AlertFeed";
import NodeTable   from "./components/NodeTable";
import { useNeith } from "./hooks/useNeith";

export default function App() {
  const { status, graph, alerts, error } = useNeith();

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>

      {/* Top bar */}
      <StatusBar status={status} error={error} />

      {/* Main grid */}
      <div style={{
        flex:    1,
        display: "grid",
        gridTemplateColumns: "1fr 320px",
        gridTemplateRows:    "1fr 1fr",
        gap:     "12px",
        padding: "12px",
        overflow: "hidden",
      }}>

        {/* Network graph — spans both rows on left */}
        <div style={{ gridRow: "1 / 3" }}>
          <NetworkGraph graph={graph} />
        </div>

        {/* Alert feed — top right */}
        <div>
          <AlertFeed alerts={alerts} />
        </div>

        {/* Node table — bottom right */}
        <div>
          <NodeTable nodes={graph.nodes} />
        </div>

      </div>
    </div>
  );
}