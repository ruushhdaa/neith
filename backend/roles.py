# backend/roles.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Live Mode Role Detection
# Job: Infer device role from observed packet behavior

from typing import Dict, Set, Optional
import ipaddress

# ── Well-known port → service map ──────────────────────────────
# When an IP receives many packets on these ports, it likely IS that service.
_SERVICE_PORTS = {
    22:    "ssh",
    53:    "dns",
    80:    "webserver",
    443:   "webserver",
    8080:  "webserver",
    8443:  "webserver",
    25:    "mailserver",
    587:   "mailserver",
    465:   "mailserver",
    3306:  "database",
    5432:  "database",
    1433:  "database",
    6379:  "database",
    27017: "database",
    21:    "fileserver",
    445:   "fileserver",
    139:   "fileserver",
    2049:  "fileserver",
    3389:  "remote_desktop",
    5900:  "remote_desktop",
}

# ── Per-IP behavior tracker ────────────────────────────────────
class RoleTracker:
    """
    Tracks observable behavior for each IP across all windows.
    Used to infer device role from traffic patterns.
    """

    def __init__(self):
        # ip → {
        #   "incoming_ports": {port: count},
        #   "outgoing_ports": {port: count},
        #   "unique_destinations": set of IPs,
        #   "unique_sources": set of IPs,
        #   "total_packets": int,
        # }
        self.stats: Dict[str, Dict] = {}

    def observe(self, src_ip: str, dst_ip: str, dst_port: int, src_port: int):
        """Called for every packet seen."""

        # Update destination IP's incoming stats
        if dst_ip not in self.stats:
            self.stats[dst_ip] = self._fresh()
        self.stats[dst_ip]["incoming_ports"][dst_port] = \
            self.stats[dst_ip]["incoming_ports"].get(dst_port, 0) + 1
        self.stats[dst_ip]["unique_sources"].add(src_ip)
        self.stats[dst_ip]["total_packets"] += 1

        # Update source IP's outgoing stats
        if src_ip not in self.stats:
            self.stats[src_ip] = self._fresh()
        self.stats[src_ip]["outgoing_ports"][dst_port] = \
            self.stats[src_ip]["outgoing_ports"].get(dst_port, 0) + 1
        self.stats[src_ip]["unique_destinations"].add(dst_ip)
        self.stats[src_ip]["total_packets"] += 1

    def _fresh(self):
        return {
            "incoming_ports": {},
            "outgoing_ports": {},
            "unique_destinations": set(),
            "unique_sources": set(),
            "total_packets": 0,
        }

    def get_role(self, ip: str) -> str:
        """
        Infer role for one IP from its observed behavior.
        Returns one of: gateway, dns, webserver, database, fileserver,
        mailserver, ssh, remote_desktop, workstation, scanner, external, unknown
        """

        # ── External (public) IPs ──────────────────────────────
        if self._is_public(ip):
            return "external"

        if ip not in self.stats:
            return "unknown"

        s = self.stats[ip]

        # ── Gateway detection ──────────────────────────────────
        # A gateway sees connections from many internal IPs
        if len(s["unique_sources"]) >= 5 and ip.endswith(".1"):
            return "gateway"

        # ── Scanner detection ──────────────────────────────────
        # An IP talking to many unique destinations rapidly = port/network scanner
        if len(s["unique_destinations"]) >= 20:
            return "scanner"

        # ── Service detection from incoming ports ──────────────
        # If majority of incoming traffic is on a known service port, it's that service
        if s["incoming_ports"]:
            top_port = max(s["incoming_ports"], key=s["incoming_ports"].get)
            top_count = s["incoming_ports"][top_port]
            total_incoming = sum(s["incoming_ports"].values())

            # Service must dominate ≥50% of incoming traffic to count
            if top_count / total_incoming >= 0.5 and top_port in _SERVICE_PORTS:
                return _SERVICE_PORTS[top_port]

        # ── Workstation fallback ───────────────────────────────
        # Initiates more than it receives → likely a client device
        outgoing = sum(s["outgoing_ports"].values())
        incoming = sum(s["incoming_ports"].values())
        if outgoing > incoming * 2:
            return "workstation"

        return "unknown"

    def _is_public(self, ip: str) -> bool:
        """Check if an IP is publicly routable (not RFC1918 / loopback / link-local)."""
        try:
            addr = ipaddress.ip_address(ip)
            return not (addr.is_private or addr.is_loopback or addr.is_link_local)
        except ValueError:
            return False
