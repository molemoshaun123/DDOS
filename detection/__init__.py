"""detection — sliding-window DDoS detector + per-bot onset estimation."""
from detection.detector import detect_ddos
from detection.onset import estimate_onsets
__all__ = ["detect_ddos", "estimate_onsets"]
