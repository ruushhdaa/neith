# backend/mitre.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: MITRE ATT&CK Mapping
# Job: Classify anomalous traffic into known adversary techniques
#
# Methodology: heuristic inference.
# We do not have ground-truth attack type labels from the live sniffer,
# so we infer the most plausible technique from observable signals:
# anomaly score magnitude, destination port, and packet-rate context.
# This is clearly a best-effort classification — not a certified mapper.

from typing import Dict, Optional

# ── Technique Registry ─────────────────────────────────────────
#
# Each entry maps a short internal key to its full ATT&CK record.
# Fields:
#   id        — ATT&CK technique ID (Txxxx or Txxxx.xxx)
#   name      — short human-readable technique name
#   tactic    — parent tactic (one per entry; techniques can have many,
#               we choose the most operationally relevant for NIDS context)
#
_TECHNIQUES: Dict[str, Dict[str, str]] = {
    "network_dos": {
        "id":     "T1498",
        "name":   "Network Denial of Service",
        "tactic": "Impact",
    },
    "endpoint_dos": {
        "id":     "T1499",
        "name":   "Endpoint Denial of Service",
        "tactic": "Impact",
    },
    "port_scan": {
        "id":     "T1046",
        "name":   "Network Service Discovery",
        "tactic": "Discovery",
    },
    "c2_beacon": {
        "id":     "T1071.001",
        "name":   "Application Layer Protocol: Web",
        "tactic": "Command and Control",
    },
    "data_exfil": {
        "id":     "T1048",
        "name":   "Exfiltration Over Alternative Protocol",
        "tactic": "Exfiltration",
    },
    "lateral_move": {
        "id":     "T1021",
        "name":   "Remote Services",
        "tactic": "Lateral Movement",
    },
    "exploit_public": {
        "id":     "T1190",
        "name":   "Exploit Public-Facing Application",
        "tactic": "Initial Access",
    },
    "recon_active": {
        "id":     "T1595",
        "name":   "Active Scanning",
        "tactic": "Reconnaissance",
    },
    "anomalous_traffic": {
        "id":     "T1205",
        "name":   "Traffic Signaling",
        "tactic": "Defense Evasion",
    },
}

# ── Port Hints ──────────────────────────────────────────────────
#
# Well-known destination ports that carry strong technique signals.
# These are secondary evidence — score magnitude takes precedence.
#
_PORT_HINTS: Dict[int, str] = {
    22:    "lateral_move",     # SSH — remote services
    23:    "lateral_move",     # Telnet — remote services
    3389:  "lateral_move",     # RDP — remote services
    445:   "lateral_move",     # SMB — lateral movement
    80:    "c2_beacon",        # HTTP — C2 over web protocol
    443:   "c2_beacon",        # HTTPS — C2 over web protocol
    8080:  "c2_beacon",        # Alt HTTP
    53:    "data_exfil",       # DNS — exfiltration via DNS tunneling
    21:    "data_exfil",       # FTP — exfiltration
    1433:  "exploit_public",   # MSSQL — public-facing exploit
    3306:  "exploit_public",   # MySQL — public-facing exploit
    6379:  "exploit_public",   # Redis — public-facing exploit
    9200:  "exploit_public",   # Elasticsearch — public-facing exploit
}

# ── Classification Logic ───────────────────────────────────────

def classify(
    score:    float,
    dst_port: Optional[int] = None,
) -> Dict[str, str]:
    """
    Return the most plausible MITRE ATT&CK technique for this alert.

    Parameters
    ----------
    score : float
        The GNN anomaly score for this node (0.0 – 1.0).
    dst_port : int | None
        The most-used destination port for this IP in this window,
        if available from the edge attributes. Optional.

    Returns
    -------
    dict with keys: id, name, tactic
    """

    # ── High-confidence: score >= 0.85 ────────────────────────
    # Extremely deviant behaviour — most likely an active attack.
    # Port context refines it; absent port defaults to network DoS
    # (the training dataset was CICIDS DDoS, so this is calibrated).
    if score >= 0.85:
        if dst_port and dst_port in _PORT_HINTS:
            key = _PORT_HINTS[dst_port]
        else:
            key = "network_dos"

    # ── Medium-high: 0.70 <= score < 0.85 ─────────────────────
    # Suspicious but not overwhelming — reconnaissance or C2 fits.
    elif score >= 0.70:
        if dst_port and dst_port in _PORT_HINTS:
            key = _PORT_HINTS[dst_port]
        elif dst_port and dst_port > 1024:
            # High ephemeral port with elevated score — port scanning heuristic
            key = "port_scan"
        else:
            key = "recon_active"

    # ── Medium: 0.60 <= score < 0.70 ──────────────────────────
    # Elevated but ambiguous — treat as general anomalous traffic.
    elif score >= 0.60:
        if dst_port and dst_port in _PORT_HINTS:
            key = _PORT_HINTS[dst_port]
        else:
            key = "anomalous_traffic"

    # ── Low-medium: 0.50 <= score < 0.60 ──────────────────────
    # Barely above threshold — weakest signal, most conservative label.
    else:
        key = "anomalous_traffic"

    return dict(_TECHNIQUES[key])


# ── Convenience Accessors ──────────────────────────────────────

def get_technique(key: str) -> Optional[Dict[str, str]]:
    """Return a technique record by its internal key, or None if unknown."""
    return dict(_TECHNIQUES[key]) if key in _TECHNIQUES else None


def all_techniques() -> Dict[str, Dict[str, str]]:
    """Return the full registry — useful for a future /api/mitre endpoint."""
    return {k: dict(v) for k, v in _TECHNIQUES.items()}
