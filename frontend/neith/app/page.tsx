"use client";

import { useState, useEffect } from "react";
import { useNeith, useNeithDrift } from "@/hooks/useNeith";
import type { NeithAlertRecord } from "@/hooks/useNeith";
import NetworkGraph from "@/components/NetworkGraph";
import LoadingScreen from "@/components/LoadingScreen";

const TABS = ["Overview", "Analysis", "Threats", "Network", "System"] as const;
type Tab = typeof TABS[number];

// Animated counter component
function AnimatedNumber({ value, color = "#F8E794" }: { value: number; color?: string }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 800;
    const steps = 40;
    const stepValue = value / steps;
    let current = 0;

    const interval = setInterval(() => {
      current += stepValue;
      if (current >= value) {
        setDisplay(value);
        clearInterval(interval);
      } else {
        setDisplay(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(interval);
  }, [value]);

  return (
    <span className="animate-count" style={{ color }}>
      {display}
    </span>
  );
}

export default function Dashboard() {
  const { status, graph, alerts, error, ready } = useNeith();
  const { events: driftEvents } = useNeithDrift();
  const [activeTab, setActiveTab] = useState<Tab>("Overview");
  const [tabFade, setTabFade] = useState(true);

  // ── Persistent alert history (SQLite-backed) ──────────────────
  const [history, setHistory] = useState<NeithAlertRecord[]>([]);
  const [historySince, setHistorySince] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchHistory = async (since?: string | null) => {
    setHistoryLoading(true);
    try {
      const url = since
        ? `http://localhost:5000/api/alerts/history?limit=50&since=${encodeURIComponent(since)}`
        : `http://localhost:5000/api/alerts/history?limit=50`;
      const res  = await fetch(url);
      const data = await res.json();
      const rows: NeithAlertRecord[] = data.alerts ?? [];
      setHistory(prev => since ? [...prev, ...rows] : rows);
      if (rows.length > 0) {
        // record_at of the last (oldest) row becomes our next page cursor
        setHistorySince(rows[rows.length - 1].recorded_at);
      }
    } catch {
      // history fetch failure is non-critical — live alerts still work
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "Threats") fetchHistory(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  if (!ready && !error) return <LoadingScreen />;

  const suspicious = graph.nodes?.filter(n => n.status === "suspicious").length ?? 0;
  const avgScore = graph.nodes?.length > 0
    ? Math.round(graph.nodes.reduce((s, n) => s + n.score, 0) / graph.nodes.length * 100)
    : 0;

  // Tab switch with fade
  const switchTab = (tab: Tab) => {
    setTabFade(false);
    setTimeout(() => {
      setActiveTab(tab);
      setTabFade(true);
    }, 150);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>

      {/* ── NAV ─────────────────────────────────────────────── */}
      <nav style={{
        position: "sticky", top: 0, zIndex: 50,
        borderBottom: "1px solid rgba(187,104,48,0.2)",
        background: "rgba(17,20,25,0.85)",
        backdropFilter: "blur(12px)",
        height: "64px",
        display: "flex", alignItems: "center",
        padding: "0 48px",
        justifyContent: "space-between",
      }}>
        {/* Logo */}
        <div className="animate-flicker">
          <span className="font-temple" style={{
            fontSize: "28px",
            color: "#F8E794",
            textShadow: "0 0 20px rgba(248,231,148,0.25)",
          }}>
            NEITH
          </span>
        </div>

        {/* Nav links */}
        <div style={{ display: "flex", gap: "40px", alignItems: "center" }}>
          {TABS.map(tab => (
            <span
              key={tab}
              onClick={() => switchTab(tab)}
              className="font-carved"
              style={{
                fontSize: "11px",
                color: activeTab === tab ? "#F8E794" : "#809070",
                cursor: "pointer",
                borderBottom: activeTab === tab ? "2px solid #BB6830" : "2px solid transparent",
                paddingBottom: "4px",
                transition: "all 0.3s ease",
              }}
            >
              {tab}
            </span>
          ))}
        </div>

        {/* Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div className="animate-pulse-dot" style={{
              width: "7px", height: "7px", borderRadius: "50%",
              background: status.status === "active" || status.status === "demo" ? "#809070" : "#BB6830",
              boxShadow: status.status === "active" || status.status === "demo"
                ? "0 0 8px rgba(128,144,112,0.8)"
                : "0 0 8px rgba(187,104,48,0.8)",
            }} />
            <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
              {status.status === "active" || status.status === "demo" ? "Neith watches" : "Neith stirs..."}
            </span>
          </div>

          {error && (
            <span className="font-carved animate-pulse-glow" style={{ fontSize: "9px", color: "#85431E" }}>
              {error}
            </span>
          )}
        </div>
      </nav>

      {/* ── CONTENT ─────────────────────────────────────────── */}
      <main style={{
        flex: 1, padding: "48px",
        opacity: tabFade ? 1 : 0,
        transition: "opacity 0.15s ease",
      }}>

        {/* ── OVERVIEW TAB ─────────────────────────────────── */}
        {activeTab === "Overview" && (
          <div className="animate-fade-in">
            {/* Dramatic heading */}
            <div style={{ marginBottom: "48px" }}>
              <h1 className="font-temple animate-flicker" style={{
                fontSize: "42px",
                color: "#F8E794",
                textShadow: "0 0 30px rgba(248,231,148,0.15)",
                marginBottom: "8px",
              }}>
                {ready ? "Neith has risen." : "The glyphs are being carved..."}
              </h1>
              <p className="font-scroll" style={{ color: "#809070", fontSize: "16px" }}>
                {ready
                  ? `The goddess perceives ${status.node_count} entities across ${status.window} windows of time.`
                  : "The temple awakens. Ancient eyes open upon the network."}
              </p>
            </div>

            {/* Two column layout */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "32px", marginBottom: "48px" }}>

              {/* Network Graph */}
              <div className="animate-border-glow" style={{
                border: "1px solid rgba(187,104,48,0.2)",
                background: "rgba(26,46,40,0.15)",
                height: "520px",
                position: "relative",
                overflow: "hidden",
              }}>
                {/* Scan overlay inside graph */}
                <div style={{
                  position: "absolute", top: 0, left: 0,
                  width: "100%", height: "3px",
                  background: "linear-gradient(90deg, transparent, rgba(248,231,148,0.2), transparent)",
                  zIndex: 10, pointerEvents: "none",
                }} className="animate-scan" />

                <div style={{
                  padding: "16px 20px",
                  borderBottom: "1px solid rgba(187,104,48,0.15)",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}>
                  <span className="font-carved" style={{ fontSize: "10px", color: "#809070" }}>
                    Live Network Topology
                  </span>
                  <span className="font-carved animate-pulse-glow" style={{ fontSize: "9px", color: "#BB6830" }}>
                    ● Scanning
                  </span>
                </div>
                <div style={{ height: "calc(100% - 49px)" }}>
                  {graph.nodes?.length > 0
                    ? <NetworkGraph nodes={graph.nodes} edges={graph.edges} />
                    : (
                      <div style={{
                        height: "100%", display: "flex",
                        alignItems: "center", justifyContent: "center",
                        flexDirection: "column", gap: "16px",
                      }}>
                        <span className="animate-breathe" style={{ fontSize: "48px" }}>𓂀</span>
                        <span className="font-carved" style={{ fontSize: "10px", color: "#809070" }}>
                          Awaiting the flow of souls...
                        </span>
                      </div>
                    )}
                </div>
              </div>

              {/* Alert Feed */}
              <div style={{
                border: "1px solid rgba(187,104,48,0.2)",
                background: "rgba(26,46,40,0.15)",
                height: "520px",
                display: "flex", flexDirection: "column",
              }}>
                <div style={{
                  padding: "16px 20px",
                  borderBottom: "1px solid rgba(187,104,48,0.15)",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}>
                  <span className="font-carved" style={{ fontSize: "10px", color: "#809070" }}>
                    Active Threats
                  </span>
                  <span className="font-carved" style={{
                    fontSize: "9px",
                    color: alerts.length > 0 ? "#85431E" : "#809070",
                  }}>
                    {alerts.length > 0
                      ? `${alerts.length} marked by the goddess`
                      : "The realm is quiet"}
                  </span>
                </div>

                <div style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
                  {alerts.length === 0 ? (
                    <div style={{
                      height: "100%", display: "flex",
                      alignItems: "center", justifyContent: "center",
                      flexDirection: "column", gap: "12px",
                    }}>
                      <span className="animate-breathe" style={{ fontSize: "36px" }}>𓊹</span>
                      <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                        No transgressors detected
                      </span>
                    </div>
                  ) : (
                    alerts.slice(0, 15).map((alert, i) => (
                      <div key={i} className={i === 0 ? "animate-alert" : ""} style={{
                        borderLeft: "2px solid #BB6830",
                        background: i === 0 ? "rgba(187,104,48,0.1)" : "rgba(187,104,48,0.05)",
                        padding: "10px 14px",
                        marginBottom: "8px",
                        animation: i < 3 ? `fade-slide-in 0.4s ease-out ${i * 0.1}s both` : "none",
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <span className="font-carved" style={{ fontSize: "11px", color: "#F8E794" }}>
                            {alert.ip}
                          </span>
                          <span className="font-carved" style={{
                            fontSize: "9px",
                            color: alert.score > 0.8 ? "#F8E794" : "#D39858",
                          }}>
                            {(alert.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "4px" }}>
                          <span className="font-scroll" style={{ fontSize: "13px", color: "#85431E" }}>
                            {i === 0 ? "Neith has just marked this node" : "Neith has marked this node"}
                          </span>
                          <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                            {alert.timestamp}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Stat blocks */}
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
              borderTop: "1px solid rgba(187,104,48,0.2)",
              borderLeft: "1px solid rgba(187,104,48,0.2)",
            }}>
              {[
                { label: "Total Nodes", value: status.node_count, color: "#F8E794" },
                { label: "Suspicious", value: suspicious, color: "#85431E" },
                { label: "Avg Risk", value: avgScore, color: "#D39858", suffix: "%" },
                { label: "Windows", value: status.window, color: "#809070" },
              ].map((stat, i) => (
                <div key={i} style={{
                  padding: "32px 28px",
                  borderRight: "1px solid rgba(187,104,48,0.2)",
                  borderBottom: "1px solid rgba(187,104,48,0.2)",
                }}>
                  <div className="font-carved" style={{
                    fontSize: "38px",
                    fontWeight: 900,
                    lineHeight: 1,
                    marginBottom: "12px",
                  }}>
                    <AnimatedNumber value={stat.value} color={stat.color} />
                    {(stat as any).suffix && <span style={{ color: stat.color, fontSize: "24px" }}>{(stat as any).suffix}</span>}
                  </div>
                  <div className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "Analysis" && (
          <div className="animate-fade-in">
            <h1 className="font-temple" style={{ fontSize: "42px", color: "#F8E794", marginBottom: "8px" }}>
              The Weighing of Souls
            </h1>
            <p className="font-scroll" style={{ color: "#809070", marginBottom: "8px" }}>
              Each node is measured against the feather of truth.
            </p>

            {/* Conformal calibration notice */}
            <p className="font-carved" style={{
              fontSize: "9px",
              color: status.conformal?.calibrated ? "#809070" : "#341E0F",
              marginBottom: "40px",
              letterSpacing: "2px",
            }}>
              {status.conformal?.calibrated
                ? `Conformal intervals active -- 90% coverage, ${status.conformal.buffer_count} calibration samples`
                : "Conformal intervals accumulating calibration samples -- point estimates shown"}
            </p>

            <div style={{
              border: "1px solid rgba(187,104,48,0.2)",
              background: "rgba(26,46,40,0.1)",
              padding: "32px",
            }}>
              <div className="font-carved" style={{ fontSize: "10px", color: "#809070", marginBottom: "24px" }}>
                Node Risk Scores -- Ranked by Severity
              </div>

              {graph.nodes?.length === 0 ? (
                <div style={{ textAlign: "center", padding: "48px 0" }}>
                  <span className="animate-breathe" style={{ fontSize: "36px" }}>𓅃</span>
                  <p className="font-carved" style={{ fontSize: "11px", color: "#809070", marginTop: "16px" }}>
                    No entities have passed through the gate
                  </p>
                </div>
              ) : (
                graph.nodes
                  ?.sort((a, b) => b.score - a.score)
                  .map((node, i) => (
                    <div key={i} style={{
                      padding: "16px 0",
                      borderBottom: "1px solid rgba(187,104,48,0.08)",
                      background: i % 2 === 0 ? "transparent" : "rgba(26,46,40,0.15)",
                      animation: `fade-slide-in 0.4s ease-out ${i * 0.05}s both`,
                    }}>
                      {/* Row: rank, IP, bar, score */}
                      <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
                        <span className="font-carved" style={{ fontSize: "9px", color: "#809070", width: "20px" }}>
                          {i + 1}
                        </span>
                        <span className="font-carved" style={{ fontSize: "11px", color: "#EACEAA", minWidth: "160px" }}>
                          {node.id}
                        </span>

                        {/* Stacked bar: interval + point score */}
                        <div style={{ flex: 1, position: "relative", height: "8px" }}>
                          {/* Confidence interval band */}
                          {(node.interval_width ?? 0) > 0 && (
                            <div style={{
                              position: "absolute",
                              left:   `${(node.score_lower ?? node.score) * 100}%`,
                              width:  `${(node.interval_width ?? 0) * 100}%`,
                              height: "100%",
                              background: node.status === "suspicious"
                                ? "rgba(187,104,48,0.18)"
                                : "rgba(128,144,112,0.18)",
                              transition: "left 1s ease, width 1s ease",
                            }} />
                          )}
                          {/* Background track */}
                          <div style={{
                            position: "absolute", top: "2px",
                            left: 0, right: 0, height: "4px",
                            background: "rgba(26,46,40,0.5)",
                          }} />
                          {/* Point score bar */}
                          <div style={{
                            position: "absolute", top: "2px",
                            left: 0, height: "4px",
                            width: `${node.score * 100}%`,
                            background: node.status === "suspicious"
                              ? "linear-gradient(90deg, #85431E, #BB6830)"
                              : "linear-gradient(90deg, #284139, #809070)",
                            transition: "width 1s ease",
                            boxShadow: node.status === "suspicious"
                              ? "0 0 6px rgba(187,104,48,0.4)" : "none",
                          }} />
                        </div>

                        <span className="font-carved" style={{
                          fontSize: "11px",
                          color: node.score > 0.8 ? "#F8E794"
                               : node.score > 0.5 ? "#D39858" : "#809070",
                          minWidth: "48px", textAlign: "right",
                        }}>
                          {(node.score * 100).toFixed(0)}%
                        </span>
                      </div>

                      {/* Interval annotation */}
                      {(node.interval_width ?? 0) > 0 && (
                        <div style={{ paddingLeft: "44px", marginTop: "4px" }}>
                          <span className="font-scroll" style={{ fontSize: "12px", color: "#732828" }}>
                            {`${((node.score_lower ?? node.score) * 100).toFixed(0)}% -- ${((node.score_upper ?? node.score) * 100).toFixed(0)}%`}
                            <span style={{ color: "#809070", marginLeft: "10px" }}>
                              90% conformal interval
                            </span>
                          </span>
                        </div>
                      )}
                    </div>
                  ))
              )}
            </div>
          </div>
        )}

        
        {activeTab === "Threats" && (
          <div className="animate-fade-in">
            <h1 className="font-temple" style={{ fontSize: "42px", color: "#F8E794", marginBottom: "8px" }}>
              The Book of Transgressors
            </h1>
            <p className="font-scroll" style={{ color: "#809070", marginBottom: "48px" }}>
              All those whom Neith has marked. Their names are written in flame.
            </p>

            <div style={{ border: "1px solid rgba(187,104,48,0.2)" }}>
              {/* ── Table header ─────────────────────────────── */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 110px 100px 90px 110px 120px 140px",
                padding: "12px 24px",
                borderBottom: "1px solid rgba(187,104,48,0.2)",
                background: "rgba(26,46,40,0.2)",
              }}>
                {["IP Address", "Role", "Score", "Window", "Time", "Technique", "Tactic"].map(h => (
                  <span key={h} className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                    {h}
                  </span>
                ))}
              </div>

              {/* ── Empty state ──────────────────────────────── */}
              {history.length === 0 && !historyLoading ? (
                <div style={{ padding: "48px 24px", textAlign: "center" }}>
                  <span className="animate-breathe" style={{ fontSize: "36px" }}>𓊹</span>
                  <p className="font-carved" style={{ fontSize: "11px", color: "#809070", marginTop: "16px" }}>
                    The book remains empty. The realm is at peace.
                  </p>
                </div>
              ) : (
                history.map((alert, i) => (
                  <div
                    key={alert.id}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 110px 100px 90px 110px 120px 140px",
                      padding: "14px 24px",
                      borderBottom: "1px solid rgba(187,104,48,0.08)",
                      borderLeft: i === 0 ? "2px solid #BB6830" : "2px solid transparent",
                      animation: `fade-slide-in 0.3s ease-out ${Math.min(i, 10) * 0.03}s both`,
                      transition: "background 0.3s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(187,104,48,0.08)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    {/* IP */}
                    <span className="font-carved" style={{ fontSize: "11px", color: "#EACEAA" }}>
                      {alert.ip}
                    </span>

                    {/* Role */}
<span className="font-carved" style={{
  fontSize: "9px",
  color: "#85431E",
  letterSpacing: "1.5px",
  textTransform: "uppercase",
}}>
  {alert.role || "—"}
</span>

                    {/* Score */}
                    <span className="font-carved" style={{
                      fontSize: "11px",
                      color: alert.score > 0.8 ? "#F8E794" : alert.score > 0.5 ? "#D39858" : "#809070",
                    }}>
                      {(alert.score * 100).toFixed(1)}%
                    </span>

                    {/* Window */}
                    <span className="font-scroll" style={{ fontSize: "14px", color: "#809070" }}>
                      #{alert.window}
                    </span>

                    {/* Time */}
                    <span className="font-scroll" style={{ fontSize: "14px", color: "#809070" }}>
                      {alert.timestamp}
                    </span>

                    {/* Technique ID — Cinzel, small, muted */}
                    <span className="font-carved" style={{
                      fontSize: "9px",
                      color: "#809070",
                      letterSpacing: "1.5px",
                    }}>
                      {alert.mitre_id ?? "—"}
                    </span>

                    {/* Tactic name — Crimson Text, slightly warmer */}
                    <span className="font-scroll" style={{
                      fontSize: "13px",
                      color: alert.tactic ? "#85431E" : "#809070",
                    }}>
                      {alert.tactic ?? "—"}
                    </span>
                  </div>
                ))
              )}

              {/* ── Load More ────────────────────────────────── */}
              {history.length > 0 && (
                <div style={{
                  borderTop: "1px solid rgba(187,104,48,0.1)",
                  padding: "16px 24px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}>
                  <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                    {history.length} records
                  </span>
                  <span
                    className="font-carved"
                    onClick={() => !historyLoading && fetchHistory(historySince)}
                    style={{
                      fontSize: "9px",
                      color: historyLoading ? "#809070" : "#BB6830",
                      cursor: historyLoading ? "default" : "pointer",
                      letterSpacing: "2px",
                      borderBottom: historyLoading ? "none" : "1px solid rgba(187,104,48,0.3)",
                      paddingBottom: "2px",
                    }}
                  >
                    {historyLoading ? "Consulting the scrolls..." : "Load Earlier Records"}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── NETWORK TAB ──────────────────────────────────── */}
        {activeTab === "Network" && (
          <div className="animate-fade-in">
            <h1 className="font-temple" style={{ fontSize: "42px", color: "#F8E794", marginBottom: "8px" }}>
              The Woven Realm
            </h1>
            <p className="font-scroll" style={{ color: "#809070", marginBottom: "32px" }}>
              Neith has woven these connections from the threads of time.
            </p>

            <div className="animate-border-glow" style={{
              border: "1px solid rgba(187,104,48,0.2)",
              height: "620px",
              position: "relative",
              overflow: "hidden",
            }}>
              {/* Scan line */}
              <div style={{
                position: "absolute", top: 0, left: 0,
                width: "100%", height: "2px",
                background: "linear-gradient(90deg, transparent, rgba(248,231,148,0.15), transparent)",
                zIndex: 10, pointerEvents: "none",
              }} className="animate-scan" />

              <div style={{
                padding: "16px 24px",
                borderBottom: "1px solid rgba(187,104,48,0.15)",
                display: "flex", justifyContent: "space-between",
              }}>
                <span className="font-carved" style={{ fontSize: "10px", color: "#809070" }}>
                  Full Network Map
                </span>
                <div style={{ display: "flex", gap: "24px" }}>
                  <span className="font-carved animate-pulse-glow" style={{ fontSize: "9px", color: "#BB6830" }}>
                    ● Live
                  </span>
                  <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                    {graph.nodes?.length ?? 0} nodes · {graph.edges?.length ?? 0} edges
                  </span>
                </div>
              </div>
              <div style={{ height: "calc(100% - 49px)" }}>
                <NetworkGraph nodes={graph.nodes ?? []} edges={graph.edges ?? []} fullscreen />
              </div>
            </div>

            {/* Legend */}
            <div style={{
              display: "flex", gap: "32px",
              marginTop: "16px", padding: "0 8px",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "rgba(40,65,57,0.8)", border: "1px solid rgba(187,104,48,0.4)" }} />
                <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>Normal Entity</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div className="animate-pulse-dot" style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#BB6830", boxShadow: "0 0 6px rgba(187,104,48,0.6)" }} />
                <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>Marked by Neith</span>
              </div>
            </div>
          </div>
        )}

        {/* -- SYSTEM TAB ------------------------------------ */}
        {activeTab === "System" && (
          <div className="animate-fade-in">
            <h1 className="font-temple" style={{ fontSize: "42px", color: "#F8E794", marginBottom: "8px" }}>
              The Inner Sanctum
            </h1>
            <p className="font-scroll" style={{ color: "#809070", marginBottom: "48px" }}>
              The mechanisms by which Neith perceives all things.
            </p>

            {/* -- Subsystem status cards -------------------- */}
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "48px" }}>
              {[
                {
                  numeral : "I",
                  name    : "Intelligence Engine",
                  desc    : "GraphSAGE Graph Neural Network trained on CICIDS 2017. 83.5% accuracy across 10,000 real network flows. The brain of the goddess.",
                  active  : status.status === "active" || status.status === "demo",
                  label   : status.status === "demo" ? "Neith dreams of past battles" : "Neith is unleashing the GNN",
                  meta    : null,
                },
                {
                  numeral : "II",
                  name    : "Drift Monitor",
                  desc    : "ADWIN adaptive windowing algorithm. Detects when network behaviour shifts so the model recalibrates automatically. The goddess adapts.",
                  active  : (status.adwin?.window_size ?? 0) > 0,
                  label   : (status.adwin?.window_size ?? 0) > 0
                              ? `Window: ${status.adwin?.window_size} obs, mean: ${((status.adwin?.current_mean ?? 0) * 100).toFixed(1)}%`
                              : "Awaiting the tides of change",
                  meta    : driftEvents.length > 0
                              ? `${driftEvents.length} drift event${driftEvents.length !== 1 ? "s" : ""} recorded`
                              : null,
                },
                {
                  numeral : "III",
                  name    : "Conformal Layer",
                  desc    : "Online split-conformal prediction. Every anomaly score carries a statistically valid 90% prediction interval. The oracle does not guess -- it bounds its uncertainty.",
                  active  : status.conformal?.calibrated ?? false,
                  label   : status.conformal?.calibrated
                              ? `Calibrated -- ${status.conformal.buffer_count} samples, sigma ${((status.conformal.std ?? 0) * 100).toFixed(1)}%`
                              : `Accumulating calibration samples (${status.conformal?.buffer_count ?? 0} of 40)`,
                  meta    : null,
                },
                {
                  numeral : "IV",
                  name    : "Persistence Layer",
                  desc    : "SQLite alert database. Every detection is written to disk and survives server restarts. The Book of Transgressors grows with time.",
                  active  : true,
                  label   : "Database ready",
                  meta    : null,
                },
              ].map((card, i) => (
                <div key={i} style={{
                  border: "1px solid rgba(187,104,48,0.2)",
                  background: "rgba(26,46,40,0.15)",
                  padding: "32px",
                  display: "flex", gap: "32px", alignItems: "flex-start",
                  position: "relative", overflow: "hidden",
                  animation: `fade-slide-in 0.5s ease-out ${i * 0.12}s both`,
                  transition: "border-color 0.3s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(187,104,48,0.5)")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "rgba(187,104,48,0.2)")}
                >
                  <div className="font-temple" style={{
                    fontSize: "96px", color: "rgba(187,104,48,0.08)",
                    position: "absolute", top: "-8px", right: "24px",
                    lineHeight: 1, pointerEvents: "none",
                  }}>
                    {card.numeral}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "12px" }}>
                      <span className="font-carved" style={{ fontSize: "13px", color: "#F8E794" }}>
                        {card.name}
                      </span>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <div className={card.active ? "animate-pulse-dot" : ""} style={{
                          width: "6px", height: "6px", borderRadius: "50%",
                          background: card.active ? "#809070" : "#341E0F",
                          boxShadow: card.active ? "0 0 8px rgba(128,144,112,0.8)" : "none",
                        }} />
                        <span className="font-carved" style={{
                          fontSize: "9px",
                          color: card.active ? "#809070" : "#341E0F",
                        }}>
                          {card.label}
                        </span>
                      </div>
                      {card.meta && (
                        <span className="font-scroll" style={{ fontSize: "13px", color: "#D39858" }}>
                          {card.meta}
                        </span>
                      )}
                    </div>
                    <p className="font-scroll" style={{ color: "#809070", fontSize: "15px", lineHeight: 1.8 }}>
                      {card.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* -- ADWIN Drift Event Log --------------------- */}
            <div style={{ border: "1px solid rgba(187,104,48,0.2)" }}>
              <div style={{
                padding: "16px 24px",
                borderBottom: "1px solid rgba(187,104,48,0.2)",
                background: "rgba(26,46,40,0.2)",
                display: "flex", justifyContent: "space-between", alignItems: "center",
              }}>
                <span className="font-carved" style={{ fontSize: "10px", color: "#809070" }}>
                  Drift Event Log
                </span>
                <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                  {driftEvents.length === 0 ? "No shifts recorded" : `${driftEvents.length} recorded`}
                </span>
              </div>

              {driftEvents.length === 0 ? (
                <div style={{ padding: "36px 24px", textAlign: "center" }}>
                  <p className="font-scroll" style={{ fontSize: "15px", color: "#809070" }}>
                    The stream flows undisturbed. No distributional shifts have been detected.
                  </p>
                </div>
              ) : (
                driftEvents.map((ev, i) => (
                  <div key={i} style={{
                    display: "grid",
                    gridTemplateColumns: "80px 100px 120px 1fr",
                    padding: "14px 24px",
                    borderBottom: "1px solid rgba(187,104,48,0.08)",
                    animation: `fade-slide-in 0.3s ease-out ${i * 0.04}s both`,
                    transition: "background 0.3s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(187,104,48,0.06)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
                      Window {ev.window}
                    </span>
                    <span className="font-scroll" style={{ fontSize: "13px", color: "#809070" }}>
                      {ev.timestamp}
                    </span>
                    <span className="font-carved" style={{ fontSize: "9px", color: "#D39858" }}>
                      avg {(ev.avg_score * 100).toFixed(1)}%
                    </span>
                    <span className="font-scroll" style={{ fontSize: "13px", color: "#85431E" }}>
                      {ev.message}
                    </span>
                  </div>
                ))
              )}
            </div>

          </div>
        )}

      </main>

      {/* ── FOOTER ──────────────────────────────────────────── */}
      <footer style={{
        borderTop: "1px solid rgba(187,104,48,0.15)",
        padding: "20px 48px",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
  NEITH · Network Entity Intelligence & Threat Hunter
  {status.status === "demo" && (
    <span style={{ color: "#D39858", marginLeft: "16px", letterSpacing: "2.5px" }}>
      · Replaying the sacred scrolls
    </span>
  )}
</span>
        <span className="font-carved" style={{ fontSize: "9px", color: "#809070" }}>
          {status.last_updated ? `Last seen: ${status.last_updated}` : "Neith watches in silence"}
        </span>
      </footer>

    </div>
  );
}