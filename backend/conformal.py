# backend/conformal.py
# NEITH -- Network Entity Intelligence & Threat Hunter
# Component: Conformal Prediction Layer
# Job: Wrap per-node GNN anomaly scores in statistically valid
#      confidence intervals using online split-conformal prediction.
#
# Method: Inductive (split) conformal prediction with a rolling calibration
# buffer.  For each new score we compute a symmetric prediction interval:
#
#   [score - q, score + q]
#
# where q is the (1 - alpha)-empirical quantile of |score - s| over all
# calibration scores s in the buffer.  The interval is clamped to [0, 1].
#
# This is distribution-free: valid under exchangeability, requires no
# Gaussian assumption, and is appropriate for the streaming setting where
# we cannot hold out a static calibration split.
#
# Reference: Venn, Gammerman, Shafer -- "Algorithmic Learning in a Random
# World", Springer 2005; Angelopoulos & Bates, "A Gentle Introduction to
# Conformal Prediction", 2021.

import threading
import math
from collections import deque
from typing import Tuple

import numpy as np


class ConformalPredictor:
    """
    Online split-conformal predictor for streaming anomaly scores.

    Parameters
    ----------
    alpha : float
        Miscoverage level.  0.1 produces 90% prediction intervals.
        Must be in (0, 1).
    buffer_size : int
        Maximum number of recent scores kept in the calibration buffer.
        Older scores are evicted automatically (deque with maxlen).
    min_calibration : int
        Minimum buffer occupancy before interval estimates are returned.
        Before this threshold is reached, predict_interval() returns the
        point estimate as a zero-width interval.
    """

    def __init__(
        self,
        alpha:           float = 0.10,
        buffer_size:     int   = 400,
        min_calibration: int   = 40,
    ):
        self._alpha           = alpha
        self._buffer_size     = buffer_size
        self._min_calibration = min_calibration
        self._buffer          = deque(maxlen=buffer_size)
        self._lock            = threading.Lock()

    # -- Calibration ------------------------------------------------

    def update(self, scores: list) -> None:
        """
        Ingest scores from a completed pipeline window.
        Call once per window with the full list of node scores.
        All values are cast to float; NaN/inf are silently ignored.
        """
        with self._lock:
            for s in scores:
                v = float(s)
                if math.isfinite(v):
                    self._buffer.append(v)

    def is_calibrated(self) -> bool:
        """True once the buffer contains enough history."""
        with self._lock:
            return len(self._buffer) >= self._min_calibration

    # -- Prediction -------------------------------------------------

    def predict_interval(self, score: float) -> Tuple[float, float, float]:
        """
        Return (lower, upper, width) for a single anomaly score.

        Before calibration threshold is reached, returns
        (score, score, 0.0) -- a degenerate point interval.
        The caller may inspect width == 0.0 to detect this case.

        The interval is clamped to [0.0, 1.0] because scores are
        bounded probabilities.
        """
        with self._lock:
            n = len(self._buffer)
            if n < self._min_calibration:
                s = round(float(score), 4)
                return (s, s, 0.0)
            calibration = np.array(self._buffer, dtype=np.float64)

        # Nonconformity scores: absolute residuals from the test point
        residuals = np.abs(calibration - float(score))

        # Finite-sample corrected quantile level
        level    = min(1.0, (1.0 - self._alpha) * (n + 1) / n)
        quantile = float(np.quantile(residuals, level, method="higher"))

        lower = round(max(0.0, float(score) - quantile), 4)
        upper = round(min(1.0, float(score) + quantile), 4)
        width = round(upper - lower, 4)

        return (lower, upper, width)

    # -- Diagnostics ------------------------------------------------

    def buffer_stats(self) -> dict:
        """Summary statistics about the current calibration buffer."""
        with self._lock:
            n = len(self._buffer)
            if n == 0:
                return {"count": 0, "mean": None, "std": None, "calibrated": False}
            arr = np.array(self._buffer, dtype=np.float64)
            return {
                "count":      n,
                "mean":       round(float(arr.mean()), 4),
                "std":        round(float(arr.std()),  4),
                "calibrated": n >= self._min_calibration,
            }
