# backend/api.py
# NEITH -- Network Entity Intelligence & Threat Hunter
# Component: Flask API
# Job: Bridge between the GNN brain and the React dashboard.
#      Integrates: GraphSAGE scoring, Conformal Prediction,
#      ADWIN Drift Detection, MITRE ATT&CK mapping, SQLite persistence,
#      and Demo Mode.

import os
from platform import node
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import threading
import time
import pickle
from datetime import datetime
from collections import deque

import numpy as np
import torch
from flask import Flask, jsonify, request
from flask_cors import CORS

from graph_builder import FlowStore, IPIndex, build_graph, start_sniffing, role_tracker
from model         import NeithBrain
from database      import init_db, insert_alert, query_alerts
from mitre         import classify
from conformal     import ConformalPredictor
from adwin         import ADWIN
from labels import get_label

# -- Configuration -----------------------------------------------
INTERFACE         = "eth0"
WINDOW_SECONDS    = 10
MODEL_PATH        = "../models/neith_trained.pt"
SCALER_PATH       = "../models/scaler.pkl"
FEATURE_COUNT     = "../models/feature_count.txt"
ALERT_THRESHOLD   = 0.70
MAX_ALERT_HISTORY = 50
MAX_DRIFT_HISTORY = 20
DEMO_MODE         = os.environ.get("NEITH_DEMO", "0") == "1"

# -- App Setup ---------------------------------------------------
app = Flask(__name__)
CORS(app)   # allow the React frontend to reach this API

# -- Shared State ------------------------------------------------
# All background threads write here; API endpoints read from here.

state = {
    "nodes"          : [],
    "edges"          : [],
    "alerts"         : deque(maxlen=MAX_ALERT_HISTORY),
    "window_count"   : 0,
    "model_status"   : "loading",
    "last_updated"   : None,
    "drift_detected" : False,
    "demo_mode"      : DEMO_MODE,
}
state_lock   = threading.Lock()
drift_events = deque(maxlen=MAX_DRIFT_HISTORY)

# -- Subsystems --------------------------------------------------
conformal_predictor = ConformalPredictor(alpha=0.10, buffer_size=400, min_calibration=40)
adwin_detector      = ADWIN(delta=0.002, min_window=15)

# -- Model Loading -----------------------------------------------
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

# -- Score a Graph -----------------------------------------------
def score_graph(graph, model, scaler, ip_index):
    """Run the trained GNN on a graph and return per-node scores.

    Applies the saved StandardScaler to node features so they match
    the training-time distribution before GNN inference.
    """
    # Scale features to match training distribution (mean=0, std=1)
    x_numpy  = graph.x.numpy()
    x_scaled = scaler.transform(x_numpy)
    x_tensor = torch.tensor(x_scaled, dtype=torch.float)

    with torch.no_grad():
        scores = model(x_tensor, graph.edge_index)
    return scores

# -- Live Pipeline Loop ------------------------------------------
def pipeline_loop(flow_store, ip_index, model, scaler, in_channels):
    """
    Runs forever in a background thread.
    Every WINDOW_SECONDS:
      1. Build graph from captured packets.
      2. Score every node with the GNN.
      3. Attach conformal prediction intervals.
      4. Update ADWIN drift detector.
      5. Classify alerts with MITRE ATT&CK.
      6. Persist alerts to SQLite.
      7. Update shared state.
    """
    window_count = 0

    while True:
        time.sleep(WINDOW_SECONDS)
        window_count += 1

        graph = build_graph(flow_store, ip_index)
        if graph is None:
            print(f"[NEITH API] Window {window_count}: No traffic.")
            continue

        # -- Score -----------------------------------------------
        scores = score_graph(graph, model, scaler, ip_index)
        
        # -- Build node list with conformal intervals ------------
        mapping    = ip_index.get_all()
        sorted_ips = sorted(mapping.items(), key=lambda item: item[1])

        raw_scores = []
        nodes      = []
        new_alerts = []

        for ip, idx in sorted_ips:
            if idx >= len(scores):
                continue

            score  = round(scores[idx].item(), 4)
            status = "suspicious" if score > ALERT_THRESHOLD else "normal"
            raw_scores.append(score)

            # Conformal interval
            lo, hi, width = conformal_predictor.predict_interval(score)

            nodes.append({
                "id"     : ip,
                "label"  : get_label(ip),
                "score"  : score,
                "status" : status,
                "score_lower"   : lo,
                "score_upper"   : hi,
                "interval_width": width,
                "role"   : role_tracker.get_role(ip),
            })

            if status == "suspicious":
                # -- MITRE classification ------------------------
                mitre = classify(score=score)
                ts    = datetime.now().astimezone().strftime("%H:%M:%S")

                alert = {
                    "ip"         : ip,
                    "role"       : role_tracker.get_role(ip),
                    "score"      : score,
                    "timestamp"  : ts,
                    "window"     : window_count,
                    "mitre_id"   : mitre["id"],
                    "mitre_name" : mitre["name"],
                    "tactic"     : mitre["tactic"],
                }
                new_alerts.append(alert)

                # -- Persist to SQLite ---------------------------
                insert_alert(
                    ip         = ip,
                    role       = role_tracker.get_role(ip),
                    score      = score,
                    window     = window_count,
                    timestamp  = ts,
                    mitre_id   = mitre["id"],
                    mitre_name = mitre["name"],
                    tactic     = mitre["tactic"],
                )

                print(
                    f"[NEITH API]  ALERT: {ip} scored {score:.4f}"
                    f"  [{mitre['id']} -- {mitre['tactic']}]"
                )

        # -- Calibrate conformal predictor -----------------------
        conformal_predictor.update(raw_scores)

        # -- ADWIN update ----------------------------------------
        avg_score      = sum(raw_scores) / len(raw_scores) if raw_scores else 0.0
        drift_detected = adwin_detector.update(avg_score)

        if drift_detected:
            event = {
                "window"    : window_count,
                "timestamp" : datetime.now().astimezone().strftime("%H:%M:%S"),
                "avg_score" : round(avg_score, 4),
                "window_n"  : adwin_detector.window_size(),
                "message"   : "Network behaviour distribution has shifted. "
                              "The model may benefit from recalibration.",
            }
            drift_events.appendleft(event)
            print(f"[NEITH API] Drift detected at window {window_count}.")

        # -- Build edge list -------------------------------------
        edge_index = graph.edge_index.t().tolist()
        ip_list    = [ip for ip, _ in sorted_ips]

        edges = []
        for src_idx, dst_idx in edge_index:
            if src_idx < len(ip_list) and dst_idx < len(ip_list):
                edges.append({
                    "source" : ip_list[src_idx],
                    "target" : ip_list[dst_idx],
                })

        # -- Update shared state ---------------------------------
        with state_lock:
            state["nodes"]          = nodes
            state["edges"]          = edges
            state["window_count"]   = window_count
            state["model_status"]   = "active"
            state["last_updated"]   = datetime.now().astimezone().strftime("%H:%M:%S")
            state["drift_detected"] = drift_detected
            for alert in new_alerts:
                state["alerts"].appendleft(alert)

        print(
            f"[NEITH API] Window {window_count}: "
            f"{len(nodes)} nodes scored, {len(new_alerts)} alerts."
        )

# -- API Endpoints -----------------------------------------------

@app.route("/api/status", methods=["GET"])
def get_status():
    """Health check and summary metrics."""
    with state_lock:
        cs = conformal_predictor.buffer_stats()
        return jsonify({
            "status"            : state["model_status"],
            "window"            : state["window_count"],
            "last_updated"      : state["last_updated"],
            "node_count"        : len(state["nodes"]),
            "alert_count"       : len(state["alerts"]),
            "demo_mode"         : state["demo_mode"],
            "drift_detected"    : state["drift_detected"],
            "conformal": {
                "calibrated"    : cs["calibrated"],
                "buffer_count"  : cs["count"],
                "mean"          : cs["mean"],
                "std"           : cs["std"],
            },
            "adwin": {
                "window_size"   : adwin_detector.window_size(),
                "current_mean"  : adwin_detector.get_mean(),
            },
        })

@app.route("/api/graph", methods=["GET"])
def get_graph():
    """Full graph -- nodes (with conformal intervals) and edges."""
    with state_lock:
        return jsonify({
            "nodes" : list(state["nodes"]),
            "edges" : list(state["edges"]),
        })

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Recent in-memory alerts with MITRE enrichment."""
    with state_lock:
        return jsonify({
            "alerts" : list(state["alerts"]),
        })

@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    """All current nodes with anomaly scores and confidence intervals."""
    with state_lock:
        return jsonify({
            "nodes" : list(state["nodes"]),
        })

@app.route("/api/alerts/history", methods=["GET"])
def get_alert_history():
    """
    Persistent alert history read from SQLite -- survives restarts.

    Query parameters
    ----------------
    limit : int   (default 100, max 500)
    since : str   ISO timestamp.  Returns records newer than this value.
                  Use the recorded_at field of the last row to page forward.
    """
    limit = request.args.get("limit", 100, type=int)
    since = request.args.get("since", None, type=str)
    rows  = query_alerts(limit=limit, since=since)
    return jsonify({
        "alerts" : rows,
        "count"  : len(rows),
    })

@app.route("/api/drift", methods=["GET"])
def get_drift():
    """
    Recent ADWIN drift events -- distribution shifts detected in the
    stream of per-window average anomaly scores.
    """
    return jsonify({
        "events"   : list(drift_events),
        "count"    : len(drift_events),
        "adwin": {
            "window_size"  : adwin_detector.window_size(),
            "current_mean" : adwin_detector.get_mean(),
            "delta"        : 0.002,
        },
    })

@app.route("/api/conformal", methods=["GET"])
def get_conformal():
    """
    Conformal predictor diagnostic -- calibration buffer statistics.
    """
    stats = conformal_predictor.buffer_stats()
    return jsonify({
        "calibrated"   : stats["calibrated"],
        "buffer_count" : stats["count"],
        "mean"         : stats["mean"],
        "std"          : stats["std"],
        "alpha"        : 0.10,
        "coverage"     : "90%",
    })

# -- Entry Point -------------------------------------------------
if __name__ == "__main__":

    # Initialise persistent storage
    init_db()

    if DEMO_MODE:
        # --------------------------------------------------------
        # Demo mode: no packet capture, no model needed.
        # Synthetic data from demo.py drives all API endpoints.
        # --------------------------------------------------------
        print("[NEITH API] Demo mode active. No hardware required.")

        from demo import run_demo_loop

        with state_lock:
            state["model_status"] = "demo"

        demo_thread = threading.Thread(
            target = run_demo_loop,
            args   = (state, state_lock, conformal_predictor,
                      adwin_detector, drift_events, WINDOW_SECONDS),
            daemon = True,
        )
        demo_thread.start()
        print("[NEITH API] Demo engine started.")

    else:
        # --------------------------------------------------------
        # Live mode: real packet capture + GNN inference.
        # --------------------------------------------------------
        model, scaler, in_channels = load_model()

        with state_lock:
            state["model_status"] = "active"

        flow_store = FlowStore()
        ip_index   = IPIndex()

        sniffer_thread = threading.Thread(
            target = start_sniffing,
            args   = (flow_store, ip_index, INTERFACE),
            daemon = True,
        )
        sniffer_thread.start()
        print("[NEITH API] Packet capture started.")

        pipeline_thread = threading.Thread(
            target = pipeline_loop,
            args   = (flow_store, ip_index, model, scaler, in_channels),
            daemon = True,
        )
        pipeline_thread.start()
        print("[NEITH API] Pipeline loop started.")

    print("[NEITH API] Starting API on http://localhost:5000")
    app.run(
        host  = "0.0.0.0",
        port  = 5000,
        debug = False,   # debug=True breaks threading
    )