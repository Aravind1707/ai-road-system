from pydantic import BaseModel

class VehicleData(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float
    severity: str
    length: float
    damage_type: str
    vibration: float = 0.0
    speed: float = 0.0
    road_type: str = "unknown"
    traffic_density: float = 1.0

    class Config:
        orm_mode = True


class ComplaintUpdate(BaseModel):
    status: str
    remarks: str = None

    class Config:
        orm_mode = True
