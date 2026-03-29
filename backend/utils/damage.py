def calculate_damage_score(severity: str, length: float, vibration: float = 0.0, traffic_density: float = 1.0, road_type: str = "unknown") -> float:
    severity_weight = {
        "Low": 1.0,
        "Medium": 2.0,
        "High": 3.0
    }

    road_type_weight = {
        "highway": 1.5,
        "primary": 1.3,
        "secondary": 1.2,
        "residential": 1.0,
        "unknown": 1.0
    }

    base = severity_weight.get(severity, 1.0) * max(0.0, length)
    vibration_factor = 1 + min(max(vibration, 0.0), 1.0) * 0.5
    density_factor = 1 + min(max(traffic_density, 0.0), 10.0) / 10.0
    rdi = base * vibration_factor * density_factor * road_type_weight.get(road_type.lower(), 1.0)

    return rdi
