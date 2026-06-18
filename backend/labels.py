# backend/labels.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: IP Labeling
# Job: Convert raw IPs to human-readable names via reverse DNS + private network detection

import socket
import ipaddress
from typing import Optional

# ── Cache ───────────────────────────────────────────────────────
# Reverse DNS lookups are slow. Cache results so we never look up
# the same IP twice in one session.
_cache: dict[str, str] = {}

# ── Friendly labels for common private network ranges ───────────
_PRIVATE_LABELS = {
    "10.": "Internal Network",
    "172.16.": "Internal Network",
    "172.17.": "Internal Network",
    "172.18.": "Internal Network",
    "172.19.": "Internal Network",
    "172.20.": "Internal Network",
    "172.21.": "Internal Network",
    "172.22.": "Internal Network",
    "172.23.": "WSL Host",
    "172.24.": "Docker Network",
    "172.25.": "Docker Network",
    "172.26.": "Docker Network",
    "172.27.": "Docker Network",
    "172.28.": "Docker Network",
    "172.29.": "Docker Network",
    "172.30.": "Docker Network",
    "172.31.": "Docker Network",
    "192.168.": "Local Network",
    "127.": "Loopback",
    "169.254.": "Link Local",
}

# ── Main Function ───────────────────────────────────────────────
def get_label(ip: str) -> Optional[str]:
    """
    Return a human-readable label for an IP address, or None if unknown.

    Strategy:
    1. Check cache
    2. Check if it's a private/internal IP → return network type
    3. Try reverse DNS lookup → return domain name
    4. Fallback: return None (UI will just show the IP)
    """

    # Cache hit
    if ip in _cache:
        return _cache[ip]

    # Private network detection
    for prefix, label in _PRIVATE_LABELS.items():
        if ip.startswith(prefix):
            _cache[ip] = label
            return label

    # Public IP — try reverse DNS
    try:
        socket.setdefaulttimeout(0.5)  # don't block the pipeline
        hostname, _, _ = socket.gethostbyaddr(ip)

        # Clean up the hostname — keep only the meaningful part
        # e.g. "lhr25s31-in-f14.1e100.net" → "google.com" (we'll simplify)
        parts = hostname.split(".")
        if len(parts) >= 2:
            # Take the last two parts: domain.tld
            label = ".".join(parts[-2:])
        else:
            label = hostname

        _cache[ip] = label
        return label

    except (socket.herror, socket.gaierror, socket.timeout, OSError):
        # No reverse DNS or lookup failed
        _cache[ip] = ""
        return None
