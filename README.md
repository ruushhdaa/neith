# NEITH
### Network Entity Intelligence & Threat Hunter

> *The Egyptian goddess Neith wove the fabric of reality and hunted across it.*
> *This system weaves your network into a living graph and hunts anomalies within it.*

---

## Live Demo

**[neith-green.vercel.app](https://neith-green.vercel.app)**

Try the full dashboard in your browser with realistic synthetic data. No installation required.

---

## See It Work

https://github.com/user-attachments/assets/bd3160dc-12b4-4415-a0e4-024e60151cbe

---

## What Is NEITH?

NEITH is an AI-powered Network Intrusion Detection System that watches your network in real time, builds a graph of every device and connection, and uses a Graph Neural Network to flag suspicious behavior — all displayed in a live Egyptian-themed war room dashboard.

It does not rely on attack signatures or hand-written rules. It learns what normal looks like and tells you when something deviates.

---

## What It Does

- **Captures** live network traffic with Scapy
- **Builds** a graph every 10 seconds (nodes = IPs, edges = connections)
- **Engineers** 28 CICIDS-aligned features per IP from raw packet observation
- **Scores** every device using a trained GraphSAGE Graph Neural Network
- **Labels** IPs via reverse DNS lookup (e.g., google.com, cloudflare.net)
- **Infers** device roles from observed behavior (gateway, webserver, scanner, workstation, external)
- **Classifies** suspicious behavior against the MITRE ATT&CK framework
- **Quantifies** uncertainty with Conformal Prediction (90% confidence intervals)
- **Detects** concept drift with ADWIN adaptive windowing
- **Persists** every alert to SQLite so nothing is lost on restart
- **Visualizes** everything in a live dashboard styled like an ancient temple

---

## Architecture

Packets (Scapy)
  → Live Feature Engineering (28-dim per IP, CICIDS-aligned)
    → Role Inference + Reverse DNS Labeling
      → Graph Builder (PyTorch Geometric)
        → StandardScaler (training distribution alignment)
          → GraphSAGE GNN (anomaly scoring)
            → Conformal Predictor (confidence intervals)
              → ADWIN Drift Monitor
                → MITRE ATT&CK Classifier
                  → SQLite Persistence
                    → Flask API
                      → Next.js Dashboard (D3.js)

---

## Stack

| Layer | Technology |
|-------|-----------|
| Packet Capture | Scapy |
| Feature Engineering | NumPy, custom CICIDS-aligned pipeline |
| Graph Construction | PyTorch Geometric |
| Intelligence | GraphSAGE (trained on CICIDS 2017, 83.5% accuracy) |
| Uncertainty | Conformal Prediction (online split-conformal) |
| Drift Detection | ADWIN (Bifet & Gavaldà 2007) |
| Threat Classification | MITRE ATT&CK heuristic mapping |
| IP Labeling | Reverse DNS + private network detection |
| Role Inference | Port-based + behavior-based heuristics |
| Persistence | SQLite (stdlib only) |
| API | Flask |
| Frontend | Next.js, TypeScript, D3.js, Tailwind CSS |
| Aesthetic | UnifrakturMaguntia, Cinzel, Crimson Text |
| Deployment | Vercel (frontend + static demo data) |

---

## Dashboard

Five tabs, each named after an Egyptian concept:

| Tab | Egyptian Name | What It Shows |
|-----|---------------|---------------|
| Overview | Neith has risen | Live network graph, alert feed, key stats |
| Analysis | The Weighing of Souls | Ranked node risk scores with conformal intervals |
| Threats | The Book of Transgressors | Persistent MITRE-classified alert history with device roles |
| Network | The Woven Realm | Full-screen network topology |
| System | The Inner Sanctum | Subsystem health, drift event log |

---

## Quick Start

### Demo Mode (no network access needed)

Perfect for trying NEITH without root privileges or live capture.

Terminal 1 — Backend:

    cd backend
    pip install -r requirements.txt
    NEITH_DEMO=1 python api.py

Terminal 2 — Frontend:

    cd frontend/neith
    npm install
    npm run dev

Open http://localhost:3000

### Live Mode (real packet capture, requires sudo)

    cd backend
    sudo python api.py

Frontend starts the same way.

In live mode, NEITH performs reverse DNS lookups on every IP, infers device roles from observed behavior, and feeds real per-IP feature vectors into the GNN.

---

## Features

### Implemented
- [x] Real-time packet capture (Scapy)
- [x] Dynamic graph construction every 10 seconds
- [x] **Live feature engineering** — per-IP CICIDS-aligned 80-dim vectors (28 real, 52 padded)
- [x] **StandardScaler** applied before GNN inference for training-distribution alignment
- [x] GraphSAGE Graph Neural Network anomaly detection
- [x] **Reverse DNS labeling** — IPs displayed with their domain names
- [x] **Device role inference** — gateway, webserver, database, scanner, workstation, external, multicast
- [x] Flask REST API (status, graph, alerts, history, drift, conformal endpoints)
- [x] Live animated dashboard with five tabs
- [x] MITRE ATT&CK heuristic classification (9 techniques across 6 tactics)
- [x] SQLite persistence — alerts survive restarts
- [x] Conformal Prediction — 90% confidence interval on every score
- [x] ADWIN drift detection with event logging
- [x] Demo mode for portfolio visitors (synthetic enterprise LAN data)
- [x] Static demo fallback for Vercel deployment

### Planned
- [ ] Mobile responsive layout
- [ ] Docker deployment
- [ ] Backend hosting (Render or Railway) for fully live web demo
- [ ] Custom training pipeline matching the live feature set
- [ ] Research paper benchmarks

---

## Honest Engineering Scope

This is a portfolio project, not a production NIDS. Some honest notes:

- **Feature coverage**: live mode computes 28 of the 80 CICIDS features the model was trained on. The remaining 52 (subflow stats, bulk transfer detection, init window bytes, active/idle analysis) require deep flow analysis beyond the current scope. Padded slots are zero. Scores reflect real packet statistics in the slots we can fill.
- **MITRE classification**: heuristic, not ML-based. Maps anomaly scores and destination ports to the most plausible technique. Honest about being a best-effort classifier.
- **Role inference**: heuristic, threshold-based. Works well on observable patterns; would miss disguised attackers.
- **Trained on DDoS only**: the GNN was trained on CICIDS 2017 Friday DDoS data. Performance on other attack types is untested.

---

## Training Results

*GraphSAGE trained on the CICIDS 2017 DDoS dataset (Friday afternoon):*

| Epoch | Loss | Accuracy |
| :--- | :---: | :---: |
| Epoch 01/10 | 0.7029 | 53.67% |
| Epoch 05/10 | 0.6431 | 69.52% |
| Epoch 10/10 | 0.5774 | 83.53% |

10,000 flows (5,000 benign + 5,000 attack), 80 features, 2-layer GraphSAGE (80 → 64 → 32 → 1), Binary Cross-Entropy loss, Adam optimizer.

---

## API Endpoints

| Endpoint | Returns |
|----------|---------|
| GET /api/status | System health, window count, subsystem state, demo flag |
| GET /api/graph | Current network graph with anomaly scores, labels, roles, and intervals |
| GET /api/alerts | In-memory active alerts (last 50) |
| GET /api/alerts/history | Persistent alert history from SQLite |
| GET /api/drift | ADWIN drift event log |
| GET /api/conformal | Conformal calibration diagnostics |

---

## Project Structure
```text
neith/
├── backend/
│   ├── api.py              # Flask API + background pipeline
│   ├── graph_builder.py    # Packet capture → graph
│   ├── live_features.py    # Per-IP CICIDS-aligned feature engineering
│   ├── labels.py           # Reverse DNS + private network labeling
│   ├── roles.py            # Device role inference from traffic
│   ├── model.py            # GraphSAGE definition
│   ├── train.py            # Offline training on CICIDS 2017
│   ├── conformal.py        # Online split-conformal predictor
│   ├── adwin.py            # ADWIN drift detection
│   ├── mitre.py            # MITRE ATT&CK heuristic classifier
│   ├── database.py         # SQLite persistence layer
│   ├── demo.py             # Synthetic data engine for demo mode
│   └── requirements.txt
├── frontend/neith/
│   ├── app/
│   │   ├── globals.css     # Animations, fonts, color system
│   │   ├── layout.tsx      # Sacred geometry, hieroglyphs background
│   │   └── page.tsx        # 5 dashboard tabs
│   ├── components/
│   │   ├── NetworkGraph.tsx
│   │   └── LoadingScreen.tsx
│   ├── hooks/
│   │   └── useNeith.ts     # API polling + static demo fallback
│   └── public/demo/        # Snapshot data for Vercel deployment
├── models/
│   ├── neith_trained.pt    # Trained GraphSAGE weights
│   ├── scaler.pkl          # Feature scaler
│   └── feature_count.txt
└── README.md
```
---

## The Aesthetic

*NEITH is styled as an Egyptian temple war room. Dark, ancient, authoritative.*

- Background: #111419 near-black with green undertone
- Sacred geometry mandala breathes faintly behind everything
- Hieroglyphs (𓂀 𓊹 𓅃 𓆑 𓄿) scattered at compass points
- Three fonts only: UnifrakturMaguntia (blackletter), Cinzel (carved Roman), Crimson Text (Renaissance serif)
- Zero rounded corners
- Zero neon, zero glassmorphism, zero generic UI

Every label is written as if a priestess is whispering through the screen.
