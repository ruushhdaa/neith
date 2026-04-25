// src/hooks/useNeith.js
// NEITH — Data fetching hook
// Polls the Flask API every 10 seconds and returns live state

import { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://localhost:5000/api";
const POLL_INTERVAL = 10000; // 10 seconds

export function useNeith() {
  const [status, setStatus] = useState({
    status: "loading",
    window: 0,
    last_updated: null,
    node_count: 0,
    alert_count: 0,
  });

  const [graph, setGraph] = useState({
    nodes: [],
    edges: [],
  });

  const [alerts, setAlerts] = useState([]);
  const [error, setError]   = useState(null);

  const fetchAll = async () => {
    try {
      const [statusRes, graphRes, alertsRes] = await Promise.all([
        axios.get(`${API_BASE}/status`),
        axios.get(`${API_BASE}/graph`),
        axios.get(`${API_BASE}/alerts`),
      ]);

      setStatus(statusRes.data);
      setGraph(graphRes.data);
      setAlerts(alertsRes.data.alerts);
      setError(null);
    } catch (err) {
      setError("Cannot reach NEITH API. Is the backend running?");
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  return { status, graph, alerts, error };
}