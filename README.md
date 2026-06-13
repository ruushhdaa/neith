# NEITH
### Network Entity Intelligence & Threat Hunter

> *The Egyptian goddess Neith wove the fabric of reality and hunted across it.*  
> *This system weaves your network into a living graph and hunts anomalies within it.*

---

## What Is NEITH?

NEITH is an AI-powered Network Intrusion Detection System that:

- **Captures** live network traffic using Scapy
- **Builds** dynamic graphs every 10 seconds (Nodes = IPs, Edges = connections)
- **Analyzes** traffic patterns using a GraphSAGE Graph Neural Network
- **Scores** every device on your network for anomalous behavior (0–100%)
- **Alerts** when suspicious patterns are detected
- **Visualizes** everything in a live Egyptian-themed dashboard

## Architecture
Packets → Graph Builder → GraphSAGE GNN → Anomaly Scores → Flask API → Dashboard

text


## Stack

| Layer | Technology |
|-------|-----------|
| Packet Capture | Scapy |
| Graph Construction | PyTorch Geometric |
| Intelligence | GraphSAGE (trained on CICIDS 2017, 83.5% accuracy) |
| API | Flask |
| Frontend | Next.js, D3.js, Tailwind CSS |
| Deployment | Linux, Raspberry Pi compatible |

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
sudo python api.py
Frontend
Bash

cd frontend/neith
npm install
npm run dev
Open http://localhost:3000

Screenshots
Coming soon

Features
 Real-time packet capture
 Dynamic graph construction
 GraphSAGE anomaly detection
 Flask REST API
 Live animated dashboard
 5 dashboard tabs (Overview, Analysis, Threats, Network, System)
 Conformal Prediction (confidence intervals)
 ADWIN Drift Detection
 MITRE ATT&CK Mapping
 Docker deployment
 Demo mode for GitHub visitors
Training Results
text

Epoch 01/10 | Loss: 0.7029 | Accuracy: 53.67%
Epoch 05/10 | Loss: 0.6431 | Accuracy: 69.52%
Epoch 10/10 | Loss: 0.5774 | Accuracy: 83.53%
Built by Rushda Jagtap
B.Tech CSE (Data Science) — MITAOE, Pune
Niche: Cyber Adversarial Analytics