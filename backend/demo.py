# backend/demo.py
# NEITH -- Network Entity Intelligence & Threat Hunter
# Component: Demo Engine
# Job: Simulate realistic network traffic and GNN outputs so the
#      full dashboard works without a live interface or root privileges.
#
# Activation: set environment variable NEITH_DEMO=1 before starting api.py.
# The engine generates synthetic per-window node/edge/alert data that
# evolves over time, approximating a real enterprise network under
# periodic attack.  All MITRE enrichment and SQLite persistence still
# execute exactly as in the live pipeline.

import math
import random
import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Tuple

from database import insert_alert
from mitre import classify
from labels import get_label

# -- Synthetic Network Topology -----------------------------------
#
# A plausible small enterprise LAN: gateway, servers, workstations,
# and three anomalous external addresses with elevated base scores.

_NODES = [
    {"ip": "192.168.1.1",   "role": "gateway",     "base": 0.08},
    {"ip": "192.168.1.2",   "role": "dns",          "base": 0.05},
    {"ip": "192.168.1.10",  "role": "fileserver",   "base": 0.12},
    {"ip": "192.168.1.20",  "role": "webserver",    "base": 0.15},
    {"ip": "192.168.1.30",  "role": "db",           "base": 0.10},
    {"ip": "192.168.1.100", "role": "workstation",  "base": 0.07},
    {"ip": "192.168.1.101", "role": "workstation",  "base": 0.06},
    {"ip": "192.168.1.102", "role": "workstation",  "base": 0.09},
    {"ip": "192.168.1.103", "role": "workstation",  "base": 0.08},
    {"ip": "10.0.0.55",     "role": "unknown",      "base": 0.35},
    {"ip": "10.0.0.201",    "role": "external",     "base": 0.45},
    {"ip": "172.16.0.99",   "role": "scanner",      "base": 0.60},
]

_EDGES_BASE = [
    ("192.168.1.100", "192.168.1.1"),
    ("192.168.1.101", "192.168.1.1"),
    ("192.168.1.102", "192.168.1.1"),
    ("192.168.1.103", "192.168.1.1"),
    ("192.168.1.1",   "192.168.1.20"),
    ("192.168.1.1",   "192.168.1.2"),
    ("192.168.1.20",  "192.168.1.30"),
    ("192.168.1.10",  "192.168.1.100"),
    ("192.168.1.10",  "192.168.1.101"),
    ("10.0.0.55",     "192.168.1.20"),
    ("10.0.0.201",    "192.168.1.1"),
    ("172.16.0.99",   "192.168.1.100"),
    ("172.16.0.99",   "192.168.1.101"),
    ("172.16.0.99",   "192.168.1.102"),
]

_ALERT_THRESHOLD = 0.50


# -- Demo Engine --------------------------------------------------

class DemoEngine:
    """
    Generates one synthetic pipeline window per tick.

    Score dynamics:
    - Each node has a base score jittered by a node-specific sine wave
      and Gaussian noise to simulate natural traffic variation.
    - Approximately every 12 windows an attack sequence is triggered
      on a randomly chosen high-base node, ramping the score above the
      alert threshold for 3-6 windows before subsiding.
    """

    def __init__(self) -> None:
        self._tick           = 0
        self._attack_active  = False
        self._attack_ip: str = ""
        self._attack_ttl     = 0

    def tick(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Advance one window.
        Returns (nodes, edges, alert_nodes).
        """
        self._tick += 1
        self._maybe_start_attack()

        nodes  = self._build_nodes()
        edges  = self._build_edges()
        alerts = [n for n in nodes if n["status"] == "suspicious"]

        if self._attack_active:
            self._attack_ttl -= 1
            if self._attack_ttl <= 0:
                self._attack_active = False
                self._attack_ip     = ""

        return nodes, edges, alerts

    # -- Attack simulation ----------------------------------------

    def _maybe_start_attack(self) -> None:
        if self._attack_active:
            return
        if random.random() < (1 / 12):
            candidates = [n for n in _NODES if n["base"] > 0.25]
            if candidates:
                chosen             = random.choice(candidates)
                self._attack_ip    = chosen["ip"]
                self._attack_active = True
                self._attack_ttl   = random.randint(3, 6)

    # -- Scoring --------------------------------------------------

    def _score(self, node: Dict) -> float:
        phase   = hash(node["ip"]) % 31
        jitter  = 0.04 * math.sin(self._tick * 0.65 + phase)
        noise   = random.gauss(0.0, 0.025)
        score   = node["base"] + jitter + noise

        if self._attack_active and node["ip"] == self._attack_ip:
            intensity = min(1.0, self._attack_ttl / 3.0)
            score    += 0.48 * intensity

        return round(max(0.0, min(1.0, score)), 4)

    # -- Builders -------------------------------------------------

    def _build_nodes(self) -> List[Dict]:
        result = []
        for node in _NODES:
            s = self._score(node)
            result.append({
                "id":     node["ip"],
                "label"  : get_label(node["ip"]),
                "score":  s,
                "status": "suspicious" if s > _ALERT_THRESHOLD else "normal",
                "role":   node["role"],
            })
        return result

    def _build_edges(self) -> List[Dict]:
        # Drop ~10% of edges each window to simulate real traffic variance
        return [
            {"source": src, "target": dst}
            for src, dst in _EDGES_BASE
            if random.random() > 0.10
        ]


# -- Demo Pipeline Loop -------------------------------------------

def run_demo_loop(
    state:         dict,
    state_lock:    threading.Lock,
    conformal,
    adwin,
    drift_events:  deque,
    window_seconds: int = 10,
) -> None:
    """
    Runs forever in a background daemon thread.
    Feeds the shared state dict each window using the same schema as
    the live pipeline_loop, so all API endpoints work identically.
    """
    engine       = DemoEngine()
    window_count = 0

    while True:
        time.sleep(window_seconds)
        window_count += 1

        nodes, edges, alert_nodes = engine.tick()

        # -- Conformal calibration --------------------------------
        all_scores = [n["score"] for n in nodes]
        conformal.update(all_scores)

        # -- Attach intervals to nodes ----------------------------
        enriched: List[Dict] = []
        for n in nodes:
            lo, hi, width = conformal.predict_interval(n["score"])
            enriched.append({
                **n,
                "score_lower":     lo,
                "score_upper":     hi,
                "interval_width":  width,
            })

        # -- ADWIN update -----------------------------------------
        avg_score      = sum(all_scores) / len(all_scores) if all_scores else 0.0
        drift_detected = adwin.update(avg_score)

        if drift_detected:
            event = {
                "window":    window_count,
                "timestamp": datetime.now().astimezone().strftime("%H:%M:%S"),
                "avg_score": round(avg_score, 4),
                "window_n":  adwin.window_size(),
                "message":   "Network behaviour distribution has shifted. "
                             "The model may benefit from recalibration.",
            }
            drift_events.appendleft(event)
            print(
                f"[NEITH DEMO] Drift at window {window_count}. "
                f"New mean: {avg_score:.4f}"
            )

        # -- Persist alerts ---------------------------------------
        new_alerts: List[Dict] = []
        for node in alert_nodes:
            mitre = classify(score=node["score"])
            ts    = datetime.now().astimezone().strftime("%H:%M:%S")
            alert = {
                "ip":         node["id"],
                "score":      node["score"],
                "timestamp":  ts,
                "window":     window_count,
                "mitre_id":   mitre["id"],
                "mitre_name": mitre["name"],
                "tactic":     mitre["tactic"],
            }
            new_alerts.append(alert)
            insert_alert(
                ip         = node["id"],
                score      = node["score"],
                window     = window_count,
                timestamp  = ts,
                mitre_id   = mitre["id"],
                mitre_name = mitre["name"],
                tactic     = mitre["tactic"],
            )

        # -- Update shared state ----------------------------------
        with state_lock:
            state["nodes"]          = enriched
            state["edges"]          = edges
            state["window_count"]   = window_count
            state["model_status"]   = "demo"
            state["last_updated"]   = datetime.now().astimezone().strftime("%H:%M:%S")
            state["drift_detected"] = drift_detected
            for alert in new_alerts:
                state["alerts"].appendleft(alert)

        print(
            f"[NEITH DEMO] Window {window_count}: "
            f"{len(enriched)} nodes, {len(new_alerts)} alerts."
        )
