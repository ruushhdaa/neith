# backend/adwin.py
# NEITH -- Network Entity Intelligence & Threat Hunter
# Component: ADWIN Concept-Drift Detector
# Job: Detect when the distribution of network anomaly scores shifts
#      so the operator knows the model may need recalibration.
#
# Algorithm: ADWIN (Adaptive Windowing), Bifet & Gavalda 2007.
# Maintains a sliding window W of recent observations.
# After each insertion it tests every cut point i in W using the
# Hoeffding inequality:  if |mean(W[0..i]) - mean(W[i..n])| >= epsilon_cut,
# the older sub-window is dropped and a drift event is reported.
#
# Scores are bounded in [0,1] so the range R = 1 (used in the Hoeffding
# bound) requires no extra normalisation.
#
# Reference: A. Bifet and R. Gavalda, "Learning from Time-Changing Data
# with Adaptive Windowing", SIAM SDM 2007.

import math
import threading
from collections import deque
from typing import Optional


class ADWIN:
    """
    Streaming concept-drift detector.

    Parameters
    ----------
    delta : float
        Statistical confidence parameter.  Lower delta => fewer false
        positives but slower detection.  Bifet & Gavalda recommend 0.002.
    min_window : int
        Minimum observations required before drift detection is active.
    """

    def __init__(self, delta: float = 0.002, min_window: int = 15):
        self._delta      = delta
        self._min_window = min_window
        self._window: deque = deque()
        self._total      = 0.0
        self._n_total    = 0      # cumulative count, used in epsilon formula
        self._lock       = threading.Lock()

    # -- Public API -------------------------------------------------

    def update(self, value: float) -> bool:
        """
        Ingest one new observation.

        Returns True if drift was detected and the window was trimmed to
        its more-recent sub-window.  Returns False otherwise.
        Caller should log a drift event when True is returned.
        """
        with self._lock:
            v = float(value)
            self._window.append(v)
            self._total   += v
            self._n_total += 1

            if len(self._window) < self._min_window:
                return False

            return self._detect_and_trim()

    def get_mean(self) -> Optional[float]:
        """Mean of the current (post-trim) window, or None if empty."""
        with self._lock:
            n = len(self._window)
            return self._total / n if n > 0 else None

    def window_size(self) -> int:
        """Number of observations in the current window."""
        with self._lock:
            return len(self._window)

    def reset(self) -> None:
        """Clear the window -- call when the model is hot-reloaded."""
        with self._lock:
            self._window.clear()
            self._total = 0.0

    # -- Internal ---------------------------------------------------

    def _epsilon_cut(self, n0: int, n1: int) -> float:
        """
        Hoeffding-bound threshold for significance of a cut.
        m = harmonic mean of n0 and n1 (ensures both sub-windows matter).
        R = 1.0 because scores live in [0, 1].
        """
        m = 1.0 / (1.0 / n0 + 1.0 / n1)
        return math.sqrt(
            (1.0 / (2.0 * m)) * math.log(4.0 * self._n_total / self._delta)
        )

    def _detect_and_trim(self) -> bool:
        """
        Scan all cut points left-to-right.
        At the first significant divergence, drop the older sub-window.
        Returns True if the window was trimmed, False if it was stable.
        """
        window_list = list(self._window)
        n           = len(window_list)
        total       = self._total

        running_sum = 0.0
        for i in range(n - 1):
            running_sum += window_list[i]
            n0    = i + 1
            n1    = n - n0
            if n0 < 2 or n1 < 2:
                continue
            mean0 = running_sum / n0
            mean1 = (total - running_sum) / n1

            if abs(mean0 - mean1) >= self._epsilon_cut(n0, n1):
                # Keep only the recent sub-window (the right portion)
                kept          = window_list[n0:]
                self._window  = deque(kept)
                self._total   = sum(kept)
                return True

        return False
