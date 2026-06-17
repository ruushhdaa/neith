# Dockerfile
# NEITH -- Network Entity Intelligence & Threat Hunter
# Backend container image.
#
# Build:  docker build -t neith-backend .
# Run:    docker run --network host --privileged -e NEITH_DEMO=1 neith-backend
#
# Notes:
#   - --network host is required for live packet capture (raw socket access).
#   - --privileged is required for Scapy to open raw sockets.
#   - For demo mode only, neither flag is needed; NEITH_DEMO=1 suffices.
#   - The models/ directory is mounted as a volume so trained weights
#     and the SQLite alert database persist across container restarts.

FROM python:3.11-slim

# -- System dependencies ----------------------------------------
# libpcap-dev: Scapy packet capture
# gcc / g++:   PyTorch Geometric C++ extension build
# curl:        health check in compose

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpcap-dev \
        libpcap0.8 \
        gcc \
        g++ \
        curl \
    && rm -rf /var/lib/apt/lists/*

# -- Working directory ------------------------------------------
WORKDIR /app

# -- Python dependencies ----------------------------------------
# Copy requirements first so Docker can cache the pip layer
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# -- Application code -------------------------------------------
COPY backend/ ./backend/
COPY models/  ./models/

# -- Expose API port --------------------------------------------
EXPOSE 5000

# -- Entry point ------------------------------------------------
WORKDIR /app/backend
CMD ["python", "api.py"]
