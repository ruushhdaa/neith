# backend/graph_builder.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Graph Builder
# Job: Watch network packets, build a graph every 60 seconds

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import threading
from collections import defaultdict
from typing import Dict, Tuple, List, Optional

import torch
from torch_geometric.data import Data
from scapy.all import sniff, IP, TCP, UDP, ARP
from model import init_model
from roles import RoleTracker

from roles import RoleTracker
from live_features import LiveFeatureTracker

# Single global role tracker for the live mode pipeline
role_tracker = RoleTracker()

# Single global live-feature tracker for GNN inference
feature_tracker = LiveFeatureTracker()

# ── Configuration ──────────────────────────────────────────────────────────────

WINDOW_SECONDS = 10
INTERFACE      = "eth0"
MAX_FLOW_EDGES = 500
FEATURE_DIM    = 6

# ── IP Address → Integer Index ─────────────────────────────────────────────────

class IPIndex:
    def __init__(self):
        self._map: Dict[str, int] = {}
        self._next_index: int = 0

    def get_or_create(self, ip: str) -> int:
        if ip not in self._map:
            self._map[ip] = self._next_index
            self._next_index += 1
        return self._map[ip]

    def get_all(self) -> Dict[str, int]:
        return dict(self._map)

    @property
    def size(self) -> int:
        return self._next_index

    def reset(self):
        self._map.clear()
        self._next_index = 0

# ── Flow Storage ───────────────────────────────────────────────────────────────

class FlowStore:
    def __init__(self):
        self._flows: Dict[Tuple[str, str], List[List[float]]] = defaultdict(list)
        self._lock = threading.Lock()

    def add_packet(self, src: str, dst: str, features: List[float]):
        with self._lock:
            self._flows[(src, dst)].append(features)

    def get_snapshot_and_reset(self) -> Dict[Tuple[str, str], List[List[float]]]:
        with self._lock:
            snapshot = dict(self._flows)
            self._flows.clear()
        return snapshot

# ── Packet Feature Extraction ──────────────────────────────────────────────────

def extract_packet_features(packet) -> Optional[Tuple[str, str, List[float]]]:
    if IP not in packet:
        return None

    src_ip   = packet[IP].src
    dst_ip   = packet[IP].dst
    pkt_size = float(len(packet))

    if TCP in packet:
        protocol = 6.0
    elif UDP in packet:
        protocol = 17.0
    else:
        protocol = 0.0

    src_port   = float(packet.sport) if hasattr(packet, 'sport') else 0.0
    dst_port   = float(packet.dport) if hasattr(packet, 'dport') else 0.0
    time_of_day = float(time.time() % 86400)

    tcp_flag = 0.0
    if TCP in packet:
        flags = packet[TCP].flags
        if flags == 0x002:
            tcp_flag = 1.0
        elif flags == 0x012:
            tcp_flag = 2.0
        elif flags == 0x001:
            tcp_flag = 3.0
        elif flags == 0x004:
            tcp_flag = 4.0

    features = [pkt_size, protocol, src_port, dst_port, time_of_day, tcp_flag]
    role_tracker.observe(src_ip, dst_ip, int(dst_port), int(src_port))
    feature_tracker.observe(
        src_ip       = src_ip,
        dst_ip       = dst_ip,
        pkt_size     = pkt_size,
        protocol     = protocol,
        src_port     = int(src_port),
        dst_port     = int(dst_port),
        tcp_flag_bits = int(tcp_flag),
    )
    return src_ip, dst_ip, features

# ── Graph Construction ─────────────────────────────────────────────────────────

def build_graph(flow_store: FlowStore, ip_index: IPIndex) -> Optional[Data]:
    snapshot = flow_store.get_snapshot_and_reset()

    if not snapshot:
        print("[NEITH] No traffic captured in this window.")
        return None

    edge_index_list = []
    edge_attr_list  = []

    sorted_flows = sorted(
        snapshot.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:MAX_FLOW_EDGES]

    for (src_ip, dst_ip), packet_features in sorted_flows:
        src_idx = ip_index.get_or_create(src_ip)
        dst_idx = ip_index.get_or_create(dst_ip)

        num_packets  = len(packet_features)
        avg_features = [
            sum(pkt[i] for pkt in packet_features) / num_packets
            for i in range(FEATURE_DIM)
        ]
        avg_features.append(float(num_packets))

        edge_index_list.append([src_idx, dst_idx])
        edge_attr_list.append(avg_features)

    if not edge_index_list:
        return None

    num_nodes = ip_index.size
    # Build real feature matrix from observed traffic.
    # IPs are sorted by ip_index order so node i corresponds to feature row i.
    sorted_ips = sorted(ip_index.get_all().items(), key=lambda x: x[1])
    ip_list    = [ip for ip, _ in sorted_ips]
    feature_matrix = feature_tracker.get_all_features(ip_list)
    x = torch.tensor(feature_matrix, dtype=torch.float)

    # Trim tracker periodically to prevent memory growth
    feature_tracker.trim(max_records_per_ip=500)
    graph = Data(
        x          = x,
        edge_index = torch.tensor(
                        edge_index_list,
                        dtype=torch.long
                     ).t().contiguous(),
        edge_attr  = torch.tensor(
                        edge_attr_list,
                        dtype=torch.float
                     ),
        num_nodes  = num_nodes,
    )

    return graph

# ── Sniffing Thread ────────────────────────────────────────────────────────────

def start_sniffing(flow_store: FlowStore, ip_index: IPIndex, interface: str):
    print(f"[NEITH] Starting packet capture on interface: {interface}")

    def handle_packet(packet):
        result = extract_packet_features(packet)
        if result:
            src, dst, features = result
            flow_store.add_packet(src, dst, features)

    sniff(
        iface  = interface,
        prn    = handle_packet,
        store  = False,
        filter = "ip",
    )

# ── Graph Window Loop ──────────────────────────────────────────────────────────

def run_graph_windows(flow_store: FlowStore, ip_index: IPIndex, brain):
    window_count = 0

    while True:
        time.sleep(WINDOW_SECONDS)
        window_count += 1

        print(f"\n[NEITH] ── Window {window_count} ──────────────────────")
        graph = build_graph(flow_store, ip_index)

        if graph is not None:
            with torch.no_grad():
                scores = brain(graph.x, graph.edge_index)

            print(f"[NEITH] Graph built with {graph.num_nodes} nodes.")

            mapping    = ip_index.get_all()
            sorted_ips = sorted(mapping.items(), key=lambda item: item[1])

            print(f"[NEITH] Anomaly Scores:")
            for ip, idx in sorted_ips:
                if idx < len(scores):
                    score  = scores[idx].item()
                    status = "⚠️  SUSPICIOUS" if score > 0.5 else "✅ NORMAL"
                    print(f"        {ip:<20} : {score:.4f}  {status}")
        else:
            print("[NEITH] Empty window — no traffic.")

# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    store = FlowStore()
    index = IPIndex()

    brain = init_model()
    brain.eval()
    print("[NEITH] Intelligence Layer initialized.")

    sniffer_thread = threading.Thread(
        target = start_sniffing,
        args   = (store, index, INTERFACE),
        daemon = True
    )
    sniffer_thread.start()

    run_graph_windows(store, index, brain)