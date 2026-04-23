# backend/model.py
# NEITH — Network Entity Intelligence & Threat Hunter
# Component: Intelligence Layer (GraphSAGE)

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

class NeithBrain(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(NeithBrain, self).__init__()
        
        # Layer 1: Aggregates features from 1-hop neighbors
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        
        # Layer 2: Aggregates from 2-hop neighbors (deeper context)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        
        # Final Layer: Produces the anomaly score (0 to 1)
        self.fc = torch.nn.Linear(out_channels, 1)

    def forward(self, x, edge_index):
        # First message passing layer + ReLU activation
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        
        # Second message passing layer
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        
        # Output a single score per node
        score = torch.sigmoid(self.fc(x))
        return score.squeeze(-1)

# Configuration for the brain
# We have 7 features per edge (from graph_builder.py)
# But since we use Zeros for node features (x) initially,
# we define the input dimension (in_channels) here.
IN_CHANNELS = 16   # The size of our initial zero-vector nodes
HIDDEN = 64
OUT = 32

def init_model():
    model = NeithBrain(IN_CHANNELS, HIDDEN, OUT)
    return model