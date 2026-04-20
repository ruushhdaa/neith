# backend/graph_builder.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Graph Builder
# Job: Watch network packets, build a graph every 60 seconds

import time
import threading
from collections import defaultdict
from typing import Dict, Tuple, List, Optional

import torch
from torch_geometric.data import Data
from scapy.all import sniff, IP, TCP, UDP, ARP

# ── Configuration ──────────────────────────────────────────────────────────────

WINDOW_SECONDS  = 10      # build a new graph every 60 seconds
INTERFACE       = "eth0"  # network interface to listen on
MAX_FLOW_EDGES  = 500     # maximum edges per graph (memory protection for Pi)
FEATURE_DIM     = 6       # number of features per edge (we define these below)

# ── IP Address → Integer Index ─────────────────────────────────────────────────
# GNNs don't understand IP addresses like "192.168.1.5"
# They understand integers like 0, 1, 2, 3
# This class converts one to the other and remembers the mapping

class IPIndex:
    def __init__(self):
        self._map: Dict[str, int] = {}
        self._next_index: int = 0

    def get_or_create(self, ip: str) -> int:
        """Give me an IP, I give you its integer index. Create one if new."""
        if ip not in self._map:
            self._map[ip] = self._next_index
            self._next_index += 1
        return self._map[ip]

    def get_all(self) -> Dict[str, int]:
        """Return the full IP → index mapping."""
        return dict(self._map)

    @property
    def size(self) -> int:
        """How many unique IPs have we seen?"""
        return self._next_index

    def reset(self):
        """Clear everything for a new time window."""
        self._map.clear()
        self._next_index = 0

# ── Flow Storage ───────────────────────────────────────────────────────────────
# A "flow" = all packets between the same source IP and destination IP
# We store raw packet features here, then aggregate them into one edge per flow

class FlowStore:
    def __init__(self):
        self._flows: Dict[Tuple[str, str], List[List[float]]] = defaultdict(list)
        self._lock = threading.Lock()

    def add_packet(self, src: str, dst: str, features: List[float]):
        """Add a packet's features to its flow bucket."""
        with self._lock:
            self._flows[(src, dst)].append(features)

    def get_snapshot_and_reset(self) -> Dict[Tuple[str, str], List[List[float]]]:
        """
        Grab everything collected so far and clear for next window.
        The lock makes sure the sniffer thread isn't writing
        at the exact moment we're reading.
        """
        with self._lock:
            snapshot = dict(self._flows)
            self._flows.clear()
        return snapshot

# ── Packet Feature Extraction ──────────────────────────────────────────────────
# Called for every single packet Scapy captures
# Extracts 6 features and stores them in FlowStore

def extract_packet_features(packet) -> Optional[Tuple[str, str, List[float]]]:
    """
    Given a raw packet, return:
    - source IP
    - destination IP  
    - list of 6 numerical features

    Returns None if packet has no IP layer (we ignore non-IP traffic)
    """
    if IP not in packet:
        return None

    src_ip  = packet[IP].src
    dst_ip  = packet[IP].dst

    # Feature 1: packet size in bytes
    pkt_size = float(len(packet))

    # Feature 2: protocol (TCP=6, UDP=17, other=0)
    if TCP in packet:
        protocol = 6.0
    elif UDP in packet:
        protocol = 17.0
    else:
        protocol = 0.0

    # Feature 3: source port (0 if no transport layer)
    src_port = float(packet.sport) if hasattr(packet, 'sport') else 0.0

    # Feature 4: destination port (0 if no transport layer)
    dst_port = float(packet.dport) if hasattr(packet, 'dport') else 0.0

    # Feature 5: time of day in seconds (0-86400)
    # Attacks often happen at unusual hours — this captures that signal
    time_of_day = float(time.time() % 86400)

    # Feature 6: TCP flags encoded as float (SYN=1, SYN-ACK=2, FIN=3, RST=4, other=0)
    # SYN floods and port scans show up in flag patterns
    tcp_flag = 0.0
    if TCP in packet:
        flags = packet[TCP].flags
        if flags == 0x002:  # SYN
            tcp_flag = 1.0
        elif flags == 0x012:  # SYN-ACK
            tcp_flag = 2.0
        elif flags == 0x001:  # FIN
            tcp_flag = 3.0
        elif flags == 0x004:  # RST
            tcp_flag = 4.0

    features = [pkt_size, protocol, src_port, dst_port, time_of_day, tcp_flag]
    return src_ip, dst_ip, features


# ── Graph Construction ─────────────────────────────────────────────────────────

def build_graph(flow_store: FlowStore, ip_index: IPIndex) -> Optional[Data]:
    """
    Take everything in FlowStore, build a PyG graph.

    Nodes = unique IP addresses
    Edges = flows between IP pairs
    Edge features = averaged packet features across all packets in that flow
    """
    snapshot = flow_store.get_snapshot_and_reset()

    if not snapshot:
        print("[NEITH] No traffic captured in this window.")
        return None

    edge_index_list = []
    edge_attr_list  = []

    # Sort flows by volume (most active flows first)
    # If we hit MAX_FLOW_EDGES, we keep the most significant ones
    sorted_flows = sorted(
        snapshot.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:MAX_FLOW_EDGES]

    for (src_ip, dst_ip), packet_features in sorted_flows:
        # Get integer indices for both IPs
        src_idx = ip_index.get_or_create(src_ip)
        dst_idx = ip_index.get_or_create(dst_ip)

        # Average all packet features for this flow into one edge feature vector
        num_packets = len(packet_features)
        avg_features = [
            sum(pkt[i] for pkt in packet_features) / num_packets
            for i in range(FEATURE_DIM)
        ]

        # Add packet count as context (how many packets in this flow?)
        # More packets = more established connection = different risk profile
        avg_features.append(float(num_packets))

        edge_index_list.append([src_idx, dst_idx])
        edge_attr_list.append(avg_features)

    if not edge_index_list:
        return None

    # Node feature matrix
    # Start with zeros — the GNN will learn node representations
    # through message passing from edge features
    num_nodes = ip_index.size
    x = torch.zeros(num_nodes, 16)

    # Build the PyG Data object
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
    """Runs forever in a background thread. Captures packets, stores features."""
    print(f"[NEITH] Starting packet capture on interface: {interface}")

    def handle_packet(packet):
        result = extract_packet_features(packet)
        if result:
            src, dst, features = result
            flow_store.add_packet(src, dst, features)

    sniff(
        iface  = interface,
        prn    = handle_packet,
        store  = False,   # critical — don't store raw packets in memory
        filter = "ip",    # only IP traffic, ignore everything else
    )

# ── Graph Window Loop ──────────────────────────────────────────────────────────

def run_graph_windows(flow_store: FlowStore, ip_index: IPIndex):
    """
    Every WINDOW_SECONDS, build a graph from collected flows.
    This is where we'll plug in the GNN later.
    """
    window_count = 0

    while True:
        time.sleep(WINDOW_SECONDS)
        window_count += 1

        print(f"\n[NEITH] ── Window {window_count} ──────────────────────")
        graph = build_graph(flow_store, ip_index)

        if graph is not None:
            print(f"[NEITH] Graph built:")
            print(f"        Nodes (unique IPs) : {graph.num_nodes}")
            print(f"        Edges (flows)      : {graph.num_edges}")
            print(f"        Edge features      : {graph.edge_attr.shape}")
            print(f"        IP mapping         : {ip_index.get_all()}")
            # GNN inference will be plugged in here next
        else:
            print("[NEITH] Empty window — no graph built.")

# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    store = FlowStore()
    index = IPIndex()

    # Start sniffer in background thread
    sniffer_thread = threading.Thread(
        target = start_sniffing,
        args   = (store, index, INTERFACE),
        daemon = True   # dies when main program exits
    )
    sniffer_thread.start()

    # Run graph windows in main thread
    run_graph_windows(store, index)

    