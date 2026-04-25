# backend/api.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Flask API
# Job: Bridge between the GNN brain and the React dashboard

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import threading
import time
import pickle
import numpy as np
from datetime import datetime
from collections import deque

import torch
from flask import Flask, jsonify
from flask_cors import CORS

from graph_builder import FlowStore, IPIndex, build_graph, start_sniffing
from model import NeithBrain

# ── Configuration ──────────────────────────────────────────────
INTERFACE        = "eth0"
WINDOW_SECONDS   = 10
MODEL_PATH       = "../models/neith_trained.pt"
SCALER_PATH      = "../models/scaler.pkl"
FEATURE_COUNT    = "../models/feature_count.txt"
ALERT_THRESHOLD  = 0.5       # score above this = suspicious
MAX_ALERT_HISTORY = 50       # keep last 50 alerts in memory

# ── App Setup ──────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)            # allows React frontend to talk to this API

# ── Shared State ───────────────────────────────────────────────
# This is the live data the API serves to the dashboard

state = {
    "nodes"         : [],     # list of {ip, score, status}
    "edges"         : [],     # list of {source, target}
    "alerts"        : deque(maxlen=MAX_ALERT_HISTORY),
    "window_count"  : 0,
    "model_status"  : "loading",
    "last_updated"  : None,
}
state_lock = threading.Lock()

# ── Load Model ─────────────────────────────────────────────────
def load_model():
    print("[NEITH API] Loading trained model...")

    with open(FEATURE_COUNT, "r") as f:
        in_channels = int(f.read().strip())

    model = NeithBrain(
        in_channels     = in_channels,
        hidden_channels = 64,
        out_channels    = 32,
    )
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    print(f"[NEITH API] Model loaded. Input features: {in_channels}")
    return model, scaler, in_channels

# ── Score A Graph ──────────────────────────────────────────────
def score_graph(graph, model, ip_index):
    """Run the trained GNN on a graph and return per-node scores."""
    with torch.no_grad():
        scores = model(graph.x, graph.edge_index)
    return scores

# ── Main Pipeline Loop ─────────────────────────────────────────
def pipeline_loop(flow_store, ip_index, model, scaler, in_channels):
    """
    Runs forever in a background thread.
    Every WINDOW_SECONDS:
      1. Build graph from captured packets
      2. Score every node with the GNN
      3. Update shared state for the API to serve
    """
    window_count = 0

    while True:
        time.sleep(WINDOW_SECONDS)
        window_count += 1

        graph = build_graph(flow_store, ip_index)

        if graph is None:
            print(f"[NEITH API] Window {window_count}: No traffic.")
            continue

        # ── Score ──────────────────────────────────────────────
        scores = score_graph(graph, model, ip_index)

        # ── Build node list ────────────────────────────────────
        mapping    = ip_index.get_all()
        sorted_ips = sorted(mapping.items(), key=lambda item: item[1])

        nodes = []
        new_alerts = []

        for ip, idx in sorted_ips:
            if idx >= len(scores):
                continue

            score  = round(scores[idx].item(), 4)
            status = "suspicious" if score > ALERT_THRESHOLD else "normal"

            nodes.append({
                "id"     : ip,
                "score"  : score,
                "status" : status,
            })

            if status == "suspicious":
                alert = {
                    "ip"        : ip,
                    "score"     : score,
                    "timestamp" : datetime.now().strftime("%H:%M:%S"),
                    "window"    : window_count,
                }
                new_alerts.append(alert)
                print(f"[NEITH API] ⚠️  ALERT: {ip} scored {score:.4f}")

        # ── Build edge list ────────────────────────────────────
        edge_index = graph.edge_index.t().tolist()
        ip_list    = [ip for ip, _ in sorted_ips]

        edges = []
        for src_idx, dst_idx in edge_index:
            if src_idx < len(ip_list) and dst_idx < len(ip_list):
                edges.append({
                    "source" : ip_list[src_idx],
                    "target" : ip_list[dst_idx],
                })

        # ── Update shared state ────────────────────────────────
        with state_lock:
            state["nodes"]        = nodes
            state["edges"]        = edges
            state["window_count"] = window_count
            state["model_status"] = "active"
            state["last_updated"] = datetime.now().strftime("%H:%M:%S")
            for alert in new_alerts:
                state["alerts"].appendleft(alert)

        print(f"[NEITH API] Window {window_count}: "
              f"{len(nodes)} nodes scored, "
              f"{len(new_alerts)} alerts.")

# ── API Endpoints ──────────────────────────────────────────────

@app.route("/api/status", methods=["GET"])
def get_status():
    """Health check — is NEITH running?"""
    with state_lock:
        return jsonify({
            "status"       : state["model_status"],
            "window"       : state["window_count"],
            "last_updated" : state["last_updated"],
            "node_count"   : len(state["nodes"]),
            "alert_count"  : len(state["alerts"]),
        })

@app.route("/api/graph", methods=["GET"])
def get_graph():
    """Full graph — nodes and edges for the network visualization."""
    with state_lock:
        return jsonify({
            "nodes" : list(state["nodes"]),
            "edges" : list(state["edges"]),
        })

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Recent alerts — suspicious IPs with scores and timestamps."""
    with state_lock:
        return jsonify({
            "alerts" : list(state["alerts"]),
        })

@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    """All current nodes with their anomaly scores."""
    with state_lock:
        return jsonify({
            "nodes" : list(state["nodes"]),
        })

# ── Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    # Load model
    model, scaler, in_channels = load_model()

    with state_lock:
        state["model_status"] = "active"

    # Packet capture shared state
    flow_store = FlowStore()
    ip_index   = IPIndex()

    # Start packet sniffer in background
    sniffer_thread = threading.Thread(
        target = start_sniffing,
        args   = (flow_store, ip_index, INTERFACE),
        daemon = True,
    )
    sniffer_thread.start()
    print("[NEITH API] Packet capture started.")

    # Start pipeline loop in background
    pipeline_thread = threading.Thread(
        target = pipeline_loop,
        args   = (flow_store, ip_index, model, scaler, in_channels),
        daemon = True,
    )
    pipeline_thread.start()
    print("[NEITH API] Pipeline loop started.")

    # Start Flask
    print("[NEITH API] Starting API on http://localhost:5000")
    app.run(
        host  = "0.0.0.0",
        port  = 5000,
        debug = False,    # debug=True breaks threading
    )