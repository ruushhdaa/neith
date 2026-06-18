"use client";

import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:5000/api";

// -- Data shapes ------------------------------------------------

export interface NeithNode {
  id: string;
  label?: string | null;
  role?: string | null;
  score: number;
  status: "normal" | "suspicious";
  score_lower?:    number;
  score_upper?:    number;
  interval_width?: number;
}

export interface NeithEdge {
  source: string;
  target: string;
}

export interface NeithAlert {
  ip:          string;
  score:       number;
  timestamp:   string;
  window:      number;
  mitre_id?:   string;
  mitre_name?: string;
  tactic?:     string;
}

// Shape returned by /api/alerts/history (SQLite-backed)
export interface NeithAlertRecord {
  id:          number;
  ip:          string;
  score:       number;
  window:      number;
  timestamp:   string;
  recorded_at: string;
  mitre_id:    string | null;
  mitre_name:  string | null;
  tactic:      string | null;
}

export interface NeithDriftEvent {
  window:    number;
  timestamp: string;
  avg_score: number;
  window_n:  number;
  message:   string;
}

export interface NeithStatus {
  status:         string;
  window:         number;
  last_updated:   string | null;
  node_count:     number;
  alert_count:    number;
  demo_mode:      boolean;
  drift_detected: boolean;
  conformal?: {
    calibrated:   boolean;
    buffer_count: number;
    mean:         number | null;
    std:          number | null;
  };
  adwin?: {
    window_size:  number;
    current_mean: number | null;
  };
}

// -- Primary hook -----------------------------------------------

export function useNeith() {
  const [status, setStatus] = useState<NeithStatus>({
    status:         "loading",
    window:         0,
    last_updated:   null,
    node_count:     0,
    alert_count:    0,
    demo_mode:      false,
    drift_detected: false,
  });
  const [graph, setGraph]   = useState<{ nodes: NeithNode[]; edges: NeithEdge[] }>({
    nodes: [],
    edges: [],
  });
  const [alerts, setAlerts] = useState<NeithAlert[]>([]);
  const [error, setError]   = useState<string | null>(null);
  const [ready, setReady]   = useState(false);

  useEffect(() => {
    const poll = async () => {
      try {
        const [s, g, a] = await Promise.all([
          axios.get(`${API}/status`),
          axios.get(`${API}/graph`),
          axios.get(`${API}/alerts`),
        ]);
        setStatus(s.data);
        setGraph(g.data);
        setAlerts(a.data.alerts ?? []);
        setError(null);
        setReady(true);
      } catch {
        setError("Neith cannot reach the mortal plane");
      }
    };

    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, []);

  return { status, graph, alerts, error, ready };
}

// -- Drift hook -------------------------------------------------

export function useNeithDrift() {
  const [events, setEvents] = useState<NeithDriftEvent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const poll = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${API}/drift`);
        setEvents(res.data.events ?? []);
      } catch {
        // non-critical -- drift panel degrades gracefully
      } finally {
        setLoading(false);
      }
    };

    poll();
    const interval = setInterval(poll, 10000);
    return () => clearInterval(interval);
  }, []);

  return { events, loading };
}
