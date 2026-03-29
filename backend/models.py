from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
from .database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, unique=True, index=True)
    device_id = Column(String, nullable=True)
    status = Column(String, default="active")
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

class GPSData(Base):
    __tablename__ = "gps_data"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class DamageData(Base):
    __tablename__ = "damage_data"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    severity = Column(String)
    length = Column(Float)
    damage_type = Column(String)
    vibration = Column(Float, default=0.0)
    speed = Column(Float, default=0.0)
    road_type = Column(String, default="unknown")
    traffic_density = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)


class Road(Base):
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)
    road_id = Column(String, unique=True, index=True)
    road_name = Column(String)
    geom = Column(String)  # WKT (PostGIS geometry layer)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="viewer")  # roles: admin, manager, vehicle
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, unique=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    damage_score = Column(Float, default=0.0)
    road_id = Column(String, index=True, nullable=True)


class RoutePoint(Base):
    __tablename__ = "route_points"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, index=True)
    vehicle_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, index=True)
    route_id = Column(Integer, nullable=True)
    vehicle_id = Column(String, index=True)
    damage_score = Column(Float)
    priority = Column(String)
    status = Column(String, default="Open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    remarks = Column(String, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    source = Column(String)
    details = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    token = Column(String, unique=True, index=True)
    is_active = Column(String, default="true")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
