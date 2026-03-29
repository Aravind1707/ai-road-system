import math
from datetime import datetime, timedelta

from .segment import get_segment_id


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def should_start_new_route(prev_ts: datetime, current_ts: datetime, prev_lat: float, prev_lon: float, current_lat: float, current_lon: float):
    if prev_ts is None:
        return True

    if current_ts - prev_ts > timedelta(minutes=5):
        return True

    if haversine_distance(prev_lat, prev_lon, current_lat, current_lon) > 200:
        return True

    return False
