from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .damage import calculate_damage_score
from .. import models


def predict_segment_future_damage(db: Session, segment_id: str, days: int = 7):
    # Collect last 30 damage records for the segment
    records = db.query(models.DamageData).filter(
        models.DamageData.latitude == db.query(models.Segment).filter(models.Segment.segment_id == segment_id).first().latitude,
        models.DamageData.longitude == db.query(models.Segment).filter(models.Segment.segment_id == segment_id).first().longitude
    ).order_by(models.DamageData.timestamp.asc()).all()

    if not records:
        return None

    points = []
    start_time = records[0].timestamp
    cumulative = 0.0
    for r in records:
        cumulative += calculate_damage_score(r.severity, r.length, vibration=getattr(r, 'vibration', 0), traffic_density=getattr(r, 'traffic_density', 1.0), road_type=getattr(r, 'road_type', 'unknown'))
        delta_days = (r.timestamp - start_time).total_seconds() / (3600.0 * 24.0)
        points.append((delta_days, cumulative))

    if len(points) < 2:
        return {
            "current_damage": cumulative,
            "predicted_damage": cumulative,
            "predicted_rdi": cumulative
        }

    x0, y0 = points[0]
    xn, yn = points[-1]
    delta_x = xn - x0 if xn - x0 > 0 else 1.0
    slope = (yn - y0) / delta_x

    predicted_damage = yn + slope * days
    return {
        "current_damage": yn,
        "predicted_damage": max(predicted_damage, yn),
        "predicted_days": days,
        "growth_rate": slope
    }
