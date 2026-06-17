# NEITH
### Network Entity Intelligence & Threat Hunter

> *The Egyptian goddess Neith wove the fabric of reality and hunted across it.*
> *This system weaves your network into a living graph and hunts anomalies within it.*

---

## What Is NEITH?

NEITH is an AI-powered Network Intrusion Detection System that watches your network in real time, builds a graph of every device and connection, and uses a Graph Neural Network to flag suspicious behavior — all displayed in a live Egyptian-themed war room dashboard.

It does not rely on attack signatures or hand-written rules. It learns what normal looks like and tells you when something deviates.

---

## What It Does

- **Captures** live network traffic with Scapy
- **Builds** a graph every 10 seconds (nodes = IPs, edges = connections)
- **Scores** every device using a trained GraphSAGE Graph Neural Network
- **Classifies** suspicious behavior against the MITRE ATT&CK framework
- **Quantifies** uncertainty with Conformal Prediction (90% confidence intervals)
- **Detects** concept drift with ADWIN adaptive windowing
- **Persists** every alert to SQLite so nothing is lost on restart
- **Visualizes** everything in a live dashboard styled like an ancient temple

---

## Architecture
Packets (Scapy)
→ Graph Builder (PyTorch Geometric)
→ GraphSAGE GNN (anomaly scoring)
→ Conformal Predictor (confidence intervals)
→ MITRE ATT&CK Classifier
→ SQLite Persistence
→ Flask API
→ Next.js Dashboard (D3.js)


---

## Stack

| Layer | Technology |
|-------|-----------|
| Packet Capture | Scapy |
| Graph Construction | PyTorch Geometric |
| Intelligence | GraphSAGE (trained on CICIDS 2017, 83.5% accuracy) |
| Uncertainty | Conformal Prediction (online split-conformal) |
| Drift Detection | ADWIN (Bifet & Gavaldà 2007) |
| Threat Classification | MITRE ATT&CK heuristic mapping |
| Persistence | SQLite (stdlib only) |
| API | Flask |
| Frontend | Next.js, TypeScript, D3.js, Tailwind CSS |
| Aesthetic | UnifrakturMaguntia, Cinzel, Crimson Text |

---

## Dashboard

Five tabs, each named after an Egyptian concept:

| Tab | Egyptian Name | What It Shows |
|-----|---------------|---------------|
| Overview | *Neith has risen* | Live network graph, alert feed, key stats |
| Analysis | *The Weighing of Souls* | Ranked node risk scores with conformal intervals |
| Threats | *The Book of Transgressors* | Persistent MITRE-classified alert history |
| Network | *The Woven Realm* | Full-screen network topology |
| System | *The Inner Sanctum* | Subsystem health, drift event log |

---

## Quick Start

### Demo Mode (no network access needed)

Perfect for trying NEITH without root privileges or live capture.

**Terminal 1 — Backend:**
```bash
cd backend
pip install -r requirements.txt
NEITH_DEMO=1 python api.py
```

**Terminal 2 — Frontend:**

```bash

cd frontend/neith
npm install
npm run dev
```

Open http://localhost:3000

---

## Live Mode (real packet capture, requires sudo)
```Bash

cd backend
sudo python api.py
Frontend starts the same way.
```

---

## Features

**Implemented**

[x] Real-time packet capture (Scapy)
[x] Dynamic graph construction every 10 seconds
[x] GraphSAGE Graph Neural Network anomaly detection
[x] Flask REST API (status, graph, alerts, history, drift, conformal endpoints)
[x] Live animated dashboard with five tabs
[x] MITRE ATT&CK heuristic classification (9 techniques across 6 tactics)
[x] SQLite persistence — alerts survive restarts
[x] Conformal Prediction — 90% confidence interval on every score
[x] ADWIN drift detection with event logging
[x] Demo mode for portfolio visitors (synthetic enterprise LAN data)

**Planned**

[ ] Mobile responsive layout
[ ] Docker deployment
[ ] Research paper benchmarks

---

## Training Results

**GraphSAGE trained on the CICIDS 2017 DDoS dataset (Friday afternoon):**



| Epoch | Loss | Accuracy |
| :--- | :---: | :---: |
| Epoch 01/10 | 0.7029 | 53.67% |
| Epoch 05/10 | 0.6431 | 69.52% |
| Epoch 10/10 | 0.5774 | 83.53% |

*10,000 flows (5,000 benign + 5,000 attack), 80 features, 2-layer GraphSAGE (80 → 64 → 32 → 1), Binary Cross-Entropy loss, Adam optimizer.*

---

## API Endpoints

| Endpoint | Returns |
| :--- | :--- |
| `GET /api/status` | System health, window count, subsystem state |
| `GET /api/graph` | Current network graph with anomaly scores and intervals |
| `GET /api/alerts` | In-memory active alerts (last 50) |
| `GET /api/alerts/history` | Persistent alert history from SQLite |
| `GET /api/drift` | ADWIN drift event log |
| `GET /api/conformal` | Conformal calibration diagnostics |

---

## Project Structure

neith/
├── backend/
│   ├── api.py              # Flask API + background pipeline
│   ├── graph_builder.py    # Packet capture → graph
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
│   └── hooks/
│       └── useNeith.ts     # API polling hooks
├── models/
│   ├── neith_trained.pt    # Trained GraphSAGE weights
│   ├── scaler.pkl          # Feature scaler
│   └── feature_count.txt
└── README.md

---

## The Aesthetic

*NEITH is styled as an Egyptian temple war room. Dark, ancient, authoritative.*

- Background: #111419 near-black with green undertone
- Sacred geometry mandala breathes faintly behind everything
- Hieroglyphs (𓂀 𓊹 𓅃 𓆑 𓄿) scattered at compass points
- Three fonts only: UnifrakturMaguntia (blackletter), Cinzel (carved Roman), Crimson Text (Renaissance serif)
- Zero rounded corners
- Zero neon, zero glassmorphism, zero generic UI
- Every label is written as if a priestess is whispering through the screen.
