# backend/train.py
# NEITH — Training Script
# Trains GraphSAGE on CICIDS 2017 DDoS data

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from torch_geometric.data import Data
from model import NeithBrain

# ── Config ─────────────────────────────────────────────────────
DATA_PATH       = "../data/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
MODEL_SAVE_PATH = "../models/neith_trained.pt"
SAMPLE_SIZE     = 10000   # use 10k rows — safe for RAM, enough to learn
EPOCHS          = 10

# ── Step 1: Load ───────────────────────────────────────────────
print("[NEITH] Loading dataset...")
df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()

print(f"[NEITH] Raw shape     : {df.shape}")
print(f"[NEITH] Label counts  :\n{df['Label'].value_counts()}")

# ── Step 2: Clean ──────────────────────────────────────────────
# Drop non-numeric columns (IP addresses, etc.)
df = df.select_dtypes(include=[np.number])

# Replace inf and NaN
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)

print(f"[NEITH] After cleaning: {df.shape}")

# ── Step 3: Labels ─────────────────────────────────────────────
# Reload labels separately before we dropped them
df_raw = pd.read_csv(DATA_PATH)
df_raw.columns = df_raw.columns.str.strip()
df_raw.replace([np.inf, -np.inf], np.nan, inplace=True)
df_raw.dropna(inplace=True)

# Align indices
df_raw = df_raw.loc[df.index]

le = LabelEncoder()
labels = le.fit_transform(df_raw["Label"])
print(f"[NEITH] Classes: {list(le.classes_)}")

# ── Step 4: Sample ─────────────────────────────────────────────
# Take balanced sample — equal BENIGN and ATTACK rows
idx_benign = np.where(labels == 0)[0]
idx_attack = np.where(labels != 0)[0]

n = min(SAMPLE_SIZE // 2, len(idx_benign), len(idx_attack))

sampled = np.concatenate([
    np.random.choice(idx_benign, n, replace=False),
    np.random.choice(idx_attack, n, replace=False),
])
np.random.shuffle(sampled)

X_sample = df.values[sampled].astype(np.float32)
y_sample = (labels[sampled] != 0).astype(np.float32)  # 1=attack, 0=benign

print(f"[NEITH] Sample shape  : {X_sample.shape}")
print(f"[NEITH] Attack ratio  : {y_sample.mean():.2%}")

# ── Step 5: Scale ──────────────────────────────────────────────
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sample)

# ── Step 6: Build a small graph ────────────────────────────────
# Nodes = rows (flows), Edges = connect every node to its 5 nearest neighbors
# For simplicity we just connect sequential nodes for now
X_tensor = torch.tensor(X_scaled, dtype=torch.float)
y_tensor = torch.tensor(y_sample, dtype=torch.float)

n_nodes = X_tensor.shape[0]

# Create simple sequential edges: 0→1, 1→2, 2→3, etc.
# This gives the GNN a graph to work with without huge memory cost
src = torch.arange(0, n_nodes - 1)
dst = torch.arange(1, n_nodes)
edge_index = torch.stack([
    torch.cat([src, dst]),
    torch.cat([dst, src])
], dim=0)

graph = Data(
    x          = X_tensor,
    edge_index = edge_index,
    y          = y_tensor,
)

print(f"[NEITH] Graph: {graph.num_nodes} nodes, {graph.num_edges} edges")

# ── Step 7: Model ──────────────────────────────────────────────
IN_CHANNELS = X_tensor.shape[1]   # however many features CICIDS has after cleaning
print(f"[NEITH] Input features: {IN_CHANNELS}")

model = NeithBrain(
    in_channels     = IN_CHANNELS,
    hidden_channels = 64,
    out_channels    = 32,
)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# ── Step 8: Train ──────────────────────────────────────────────
print("\n[NEITH] Training started...")
model.train()

for epoch in range(EPOCHS):
    optimizer.zero_grad()
    scores = model(graph.x, graph.edge_index)
    loss   = F.binary_cross_entropy(scores, graph.y)
    loss.backward()
    optimizer.step()

    # Accuracy
    preds    = (scores > 0.5).float()
    accuracy = (preds == graph.y).float().mean().item()
    print(f"  Epoch {epoch+1:02d}/{EPOCHS} | Loss: {loss.item():.4f} | Accuracy: {accuracy:.2%}")

# ── Step 9: Save ───────────────────────────────────────────────
os.makedirs("../models", exist_ok=True)
torch.save(model.state_dict(), MODEL_SAVE_PATH)

# Save scaler and feature count for inference
import pickle
with open("../models/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

with open("../models/feature_count.txt", "w") as f:
    f.write(str(IN_CHANNELS))

print(f"\n[NEITH] Model saved  → {MODEL_SAVE_PATH}")
print(f"[NEITH] Scaler saved → ../models/scaler.pkl")
print(f"[NEITH] Training complete.")