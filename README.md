# NEITH
### Network Entity Intelligence & Threat Hunter

> *The Egyptian goddess Neith wove the fabric of reality and hunted across it.*
> *This system weaves your network into a living graph and hunts anomalies within it.*

---

## Status
🔨 **Active Development** — Building in public. Follow along.

## What Is NEITH?
NEITH is an AI-powered Network Intrusion Detection System that models network 
traffic as a dynamic graph, uses a Graph Neural Network to detect behavioral 
anomalies without requiring labeled attack data, attaches statistically 
guaranteed confidence intervals to every prediction using Conformal Prediction, 
and handles network behavior changes over time using adaptive drift detection.

Fully local. No cloud dependency. Raspberry Pi deployable.

## Architecture
- **Packet Layer** — Scapy-based real-time traffic capture
- **Graph Layer** — Dynamic graph construction (Nodes = IPs, Edges = Flows)
- **Intelligence Layer** — GraphSAGE GNN anomaly detection
- **Honesty Layer** — Conformal Prediction confidence intervals
- **Resilience Layer** — ADWIN drift detection and selective retraining
- **Interface Layer** — React dashboard with live network visualization

## Stack
Python • PyTorch Geometric • Scapy • Flask • React • ONNX Runtime • River • MAPIE

## Deployment
Runs on Linux. Deployable on Raspberry Pi 4 (4GB+). No GPU required.

---

*Rushda Jagtap — First Year B.Tech CSE (Data Science), MITAOE*
