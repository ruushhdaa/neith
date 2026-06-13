"use client";

import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:5000/api";

export interface NeithNode {
  id: string;
  score: number;
  status: "normal" | "suspicious";
}

export interface NeithEdge {
  source: string;
  target: string;
}

export interface NeithAlert {
  ip: string;
  score: number;
  timestamp: string;
  window: number;
}

export interface NeithStatus {
  status: string;
  window: number;
  last_updated: string | null;
  node_count: number;
  alert_count: number;
}

export function useNeith() {
  const [status, setStatus] = useState<NeithStatus>({
    status: "loading",
    window: 0,
    last_updated: null,
    node_count: 0,
    alert_count: 0,
  });
  const [graph, setGraph] = useState<{ nodes: NeithNode[]; edges: NeithEdge[] }>({
    nodes: [],
    edges: [],
  });
  const [alerts, setAlerts] = useState<NeithAlert[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [s, g, a] = await Promise.all([
          axios.get(`${API}/status`),
          axios.get(`${API}/graph`),
          axios.get(`${API}/alerts`),
        ]);
        setStatus(s.data);
        setGraph(g.data);
        setAlerts(a.data.alerts || []);
        setError(null);
        setReady(true);
      } catch {
        setError("Neith cannot reach the mortal plane");
      }
    };

    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);

  return { status, graph, alerts, error, ready };
}
