def get_segment_id(lat: float, lon: float) -> str:
    # 4 decimal precision ~ 11 meters; adjust according to route granularity needs
    return f"{round(lat, 4)}_{round(lon, 4)}"
