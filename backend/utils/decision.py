from typing import Tuple

# Thresholds for RDI and per-segment damage score
CRITICAL_DAMAGE_THRESHOLD = 150.0
MODERATE_DAMAGE_THRESHOLD = 70.0


def get_segment_status(damage_score: float) -> Tuple[str, str]:
    if damage_score >= CRITICAL_DAMAGE_THRESHOLD:
        return "Critical", "Immediate Repair"
    if damage_score >= MODERATE_DAMAGE_THRESHOLD:
        return "Moderate", "Schedule Repair"
    return "Low", "Monitor"
