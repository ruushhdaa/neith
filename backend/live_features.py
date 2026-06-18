# backend/live_features.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Live Feature Engineering
# Job: Convert observed packet stream into 80-dim feature vector per IP
#      matching CICIDS 2017 column order so the trained GNN can score it.
#
# Honest scope: we fill ~25 of the 80 features from raw packet data.
# The remaining ~55 (subflow stats, bulk transfer detection, init window
# bytes, active/idle analysis) require deep flow analysis we don't replicate.
# Those slots stay zero. The model gets real signal in the slots it can use.

from typing import Dict, List, Optional
import numpy as np
import time
from collections import defaultdict

# ── CICIDS column → vector index map ───────────────────────────
# After train.py drops non-numeric columns (Flow ID, Source IP, Destination
# IP, Timestamp, Label), the remaining 80 features land at these indices.
# Index 0 = "Source Port", index 79 = "Idle Min".
#
# We only list the slots we actually fill. Everything else stays zero.
FEATURE_INDEX = {
    "src_port":             0,   # Source Port
    "dst_port":             1,   # Destination Port
    "protocol":             2,   # Protocol
    "flow_duration":        3,   # Flow Duration
    "total_fwd_packets":    4,   # Total Fwd Packets
    "total_bwd_packets":    5,   # Total Backward Packets
    "total_len_fwd":        6,   # Total Length of Fwd Packets
    "total_len_bwd":        7,   # Total Length of Bwd Packets
    "fwd_pkt_len_max":      8,   # Fwd Packet Length Max
    "fwd_pkt_len_min":      9,   # Fwd Packet Length Min
    "fwd_pkt_len_mean":     10,  # Fwd Packet Length Mean
    "fwd_pkt_len_std":      11,  # Fwd Packet Length Std
    "bwd_pkt_len_max":      12,  # Bwd Packet Length Max
    "bwd_pkt_len_min":      13,  # Bwd Packet Length Min
    "bwd_pkt_len_mean":     14,  # Bwd Packet Length Mean
    "flow_bytes_per_sec":   16,  # Flow Bytes/s
    "flow_pkts_per_sec":    17,  # Flow Packets/s
    "min_pkt_length":       40,  # Min Packet Length
    "max_pkt_length":       41,  # Max Packet Length
    "pkt_length_mean":      42,  # Packet Length Mean
    "pkt_length_std":       43,  # Packet Length Std
    "pkt_length_variance":  44,  # Packet Length Variance
    "fin_flag_count":       45,  # FIN Flag Count
    "syn_flag_count":       46,  # SYN Flag Count
    "rst_flag_count":       47,  # RST Flag Count
    "psh_flag_count":       48,  # PSH Flag Count
    "ack_flag_count":       49,  # ACK Flag Count
    "urg_flag_count":       50,  # URG Flag Count
    "avg_pkt_size":         54,  # Average Packet Size
}

FEATURE_DIM = 80


class LiveFeatureTracker:
    """
    Tracks per-IP packet statistics across all observed traffic.
    Produces an 80-dim CICIDS-aligned feature vector on demand.
    """

    def __init__(self):
        # ip → list of observed packet records
        # each record: dict with size, protocol, src_port, dst_port,
        #              direction ("fwd" or "bwd"), tcp_flag_bits, timestamp
        self.records: Dict[str, List[Dict]] = defaultdict(list)
        self.first_seen: Dict[str, float] = {}

    def observe(
        self,
        src_ip: str,
        dst_ip: str,
        pkt_size: float,
        protocol: float,
        src_port: int,
        dst_port: int,
        tcp_flag_bits: int,
    ):
        """Called for every packet captured."""
        now = time.time()

        # Record from the source IP's perspective (this packet is outgoing for src)
        self.records[src_ip].append({
            "size":       pkt_size,
            "protocol":   protocol,
            "src_port":   src_port,
            "dst_port":   dst_port,
            "direction":  "fwd",
            "tcp_flags":  tcp_flag_bits,
            "ts":         now,
        })

        # And from the destination IP's perspective (this packet is incoming/bwd for dst)
        self.records[dst_ip].append({
            "size":       pkt_size,
            "protocol":   protocol,
            "src_port":   dst_port,    # swap from this IP's perspective
            "dst_port":   src_port,
            "direction":  "bwd",
            "tcp_flags":  tcp_flag_bits,
            "ts":         now,
        })

        # First-seen timestamps for flow duration math
        if src_ip not in self.first_seen:
            self.first_seen[src_ip] = now
        if dst_ip not in self.first_seen:
            self.first_seen[dst_ip] = now

    def get_features(self, ip: str) -> np.ndarray:
        """
        Return an 80-dim numpy array of CICIDS-aligned features for this IP.
        Slots we can't compute stay zero.
        """
        vec = np.zeros(FEATURE_DIM, dtype=np.float32)

        recs = self.records.get(ip, [])
        if not recs:
            return vec

        # Split fwd / bwd
        fwd = [r for r in recs if r["direction"] == "fwd"]
        bwd = [r for r in recs if r["direction"] == "bwd"]

        all_sizes = [r["size"] for r in recs]
        fwd_sizes = [r["size"] for r in fwd]
        bwd_sizes = [r["size"] for r in bwd]

        # ── Port and protocol — use most recent record ─────────
        last = recs[-1]
        vec[FEATURE_INDEX["src_port"]]   = float(last["src_port"])
        vec[FEATURE_INDEX["dst_port"]]   = float(last["dst_port"])
        vec[FEATURE_INDEX["protocol"]]   = float(last["protocol"])

        # ── Flow duration & rates ──────────────────────────────
        first_ts = self.first_seen.get(ip, recs[0]["ts"])
        duration = max(recs[-1]["ts"] - first_ts, 1e-6)  # avoid div-by-zero
        total_bytes = float(sum(all_sizes))
        total_pkts  = float(len(recs))

        vec[FEATURE_INDEX["flow_duration"]]      = duration * 1_000_000  # CICIDS uses microseconds
        vec[FEATURE_INDEX["flow_bytes_per_sec"]] = total_bytes / duration
        vec[FEATURE_INDEX["flow_pkts_per_sec"]]  = total_pkts / duration

        # ── Forward direction stats ────────────────────────────
        vec[FEATURE_INDEX["total_fwd_packets"]] = float(len(fwd))
        vec[FEATURE_INDEX["total_len_fwd"]]     = float(sum(fwd_sizes))

        if fwd_sizes:
            vec[FEATURE_INDEX["fwd_pkt_len_max"]]  = float(np.max(fwd_sizes))
            vec[FEATURE_INDEX["fwd_pkt_len_min"]]  = float(np.min(fwd_sizes))
            vec[FEATURE_INDEX["fwd_pkt_len_mean"]] = float(np.mean(fwd_sizes))
            vec[FEATURE_INDEX["fwd_pkt_len_std"]]  = float(np.std(fwd_sizes))

        # ── Backward direction stats ───────────────────────────
        vec[FEATURE_INDEX["total_bwd_packets"]] = float(len(bwd))
        vec[FEATURE_INDEX["total_len_bwd"]]     = float(sum(bwd_sizes))

        if bwd_sizes:
            vec[FEATURE_INDEX["bwd_pkt_len_max"]]  = float(np.max(bwd_sizes))
            vec[FEATURE_INDEX["bwd_pkt_len_min"]]  = float(np.min(bwd_sizes))
            vec[FEATURE_INDEX["bwd_pkt_len_mean"]] = float(np.mean(bwd_sizes))

        # ── Combined packet-length statistics ──────────────────
        if all_sizes:
            vec[FEATURE_INDEX["min_pkt_length"]]      = float(np.min(all_sizes))
            vec[FEATURE_INDEX["max_pkt_length"]]      = float(np.max(all_sizes))
            vec[FEATURE_INDEX["pkt_length_mean"]]     = float(np.mean(all_sizes))
            vec[FEATURE_INDEX["pkt_length_std"]]      = float(np.std(all_sizes))
            vec[FEATURE_INDEX["pkt_length_variance"]] = float(np.var(all_sizes))
            vec[FEATURE_INDEX["avg_pkt_size"]]        = float(np.mean(all_sizes))

        # ── TCP flag counts ────────────────────────────────────
        # tcp_flag_bits values from graph_builder:
        # 1=SYN, 2=SYN-ACK, 3=FIN, 4=RST. PSH/ACK/URG not tracked yet → leave zero.
        syn_count = sum(1 for r in recs if r["tcp_flags"] in (1, 2))
        fin_count = sum(1 for r in recs if r["tcp_flags"] == 3)
        rst_count = sum(1 for r in recs if r["tcp_flags"] == 4)

        vec[FEATURE_INDEX["syn_flag_count"]] = float(syn_count)
        vec[FEATURE_INDEX["fin_flag_count"]] = float(fin_count)
        vec[FEATURE_INDEX["rst_flag_count"]] = float(rst_count)

        return vec

    def get_all_features(self, ip_list: List[str]) -> np.ndarray:
        """Return a (num_ips, 80) matrix in the order of ip_list."""
        return np.stack([self.get_features(ip) for ip in ip_list])

    def trim(self, max_records_per_ip: int = 1000):
        """
        Prevent unbounded memory growth.
        Keep only the most recent max_records_per_ip per IP.
        Call periodically from the pipeline loop.
        """
        for ip in list(self.records.keys()):
            if len(self.records[ip]) > max_records_per_ip:
                self.records[ip] = self.records[ip][-max_records_per_ip:]
