from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from .. import models, schemas
from ..utils.segment import get_segment_id
from ..utils.damage import calculate_damage_score
from ..utils.decision import get_segment_status
from ..utils.route import should_start_new_route
from fastapi import UploadFile, File
from ..utils.prediction import predict_segment_future_damage
from ..utils.emailer import send_authority_report
from ..utils.gov_api import send_gov_report
from ..utils.yolo_inference import infer_image_bytes
from ..utils.yolo_training import train_yolo_model, evaluate_yolo_model
from ..utils.lstm_trend import train_lstm_model, predict_lstm
from ..utils.report import generate_complaint_pdf
from ..routes.deps import get_db, require_role
from ..utils.audit import log_event

router = APIRouter(prefix="/vehicle", tags=["vehicle"])


@router.post("/upload")
def upload_data(data: schemas.VehicleData, auth=Depends(require_role(["vehicle", "admin", "manager"])), db: Session = Depends(get_db)):
    # Persist vehicle metadata
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.vehicle_id == data.vehicle_id).first()
    if not vehicle:
        vehicle = models.Vehicle(vehicle_id=data.vehicle_id, last_seen=datetime.utcnow())
        db.add(vehicle)
    else:
        vehicle.last_seen = datetime.utcnow()

    # Persist GPS data point
    gps_entry = models.GPSData(
        vehicle_id=data.vehicle_id,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=datetime.utcnow()
    )
    db.add(gps_entry)

    # Route builder: find active route or create
    active_route = db.query(models.Route).filter(
        models.Route.vehicle_id == data.vehicle_id,
        models.Route.end_time == None
    ).order_by(models.Route.start_time.desc()).first()

    # Locate last route point for route continuity checks
    last_point = None
    if active_route:
        last_point = db.query(models.RoutePoint).filter(models.RoutePoint.route_id == active_route.id)
        last_point = last_point.order_by(models.RoutePoint.timestamp.desc()).first()

    if (not active_route) or (last_point and should_start_new_route(last_point.timestamp, datetime.utcnow(), last_point.latitude, last_point.longitude, data.latitude, data.longitude)):
        if active_route:
            active_route.end_time = datetime.utcnow()
        active_route = models.Route(vehicle_id=data.vehicle_id, start_time=datetime.utcnow(), end_time=None)
        db.add(active_route)
        db.flush()

    route_point = models.RoutePoint(
        route_id=active_route.id,
        vehicle_id=data.vehicle_id,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=datetime.utcnow()
    )
    db.add(route_point)

    # Segment mapping
    segment_id = get_segment_id(data.latitude, data.longitude)
    segment = db.query(models.Segment).filter(models.Segment.segment_id == segment_id).first()
    if not segment:
        segment = models.Segment(segment_id=segment_id, latitude=data.latitude, longitude=data.longitude, damage_score=0.0)
        db.add(segment)

    # GIS road mapping
    from ..utils.gis import get_road_name_from_gps
    road_name = get_road_name_from_gps(data.latitude, data.longitude)
    if road_name:
        road = db.query(models.Road).filter(models.Road.road_name == road_name).first()
        if not road:
            # Use segment_id as fallback for road_id
            road = models.Road(road_id=segment_id, road_name=road_name, geom=f"POINT({data.longitude} {data.latitude})")
            db.add(road)
        segment.road_id = road.road_id

    # Calculate and update damage (RDI includes road type + traffic density + vibration)
    damage_score = calculate_damage_score(data.severity, data.length, vibration=data.vibration, traffic_density=data.traffic_density, road_type=data.road_type)
    segment.damage_score += damage_score

    # Persist damage record
    damage_entry = models.DamageData(
        vehicle_id=data.vehicle_id,
        latitude=data.latitude,
        longitude=data.longitude,
        severity=data.severity,
        length=data.length,
        damage_type=data.damage_type,
        vibration=data.vibration,
        speed=data.speed,
        road_type=data.road_type,
        traffic_density=data.traffic_density,
        timestamp=datetime.utcnow()
    )
    db.add(damage_entry)

    db.commit()
    db.refresh(segment)

    # Segment decision
    segment_severity, recommendation = get_segment_status(segment.damage_score)

    # complaint generation for critical segments
    if segment_severity == "Critical":
        existing = db.query(models.Complaint).filter(
            models.Complaint.segment_id == segment.segment_id,
            models.Complaint.status.in_(["Open", "In Progress"])
        ).first()
        if not existing:
            complaint = models.Complaint(
                segment_id=segment.segment_id,
                route_id=active_route.id,
                vehicle_id=data.vehicle_id,
                damage_score=segment.damage_score,
                priority="High",
                status="Open",
                remarks="Auto-generated critical damage alert"
            )
            db.add(complaint)
            db.commit()

            # Auto-send notification to authority and store audit
            subject = f"Urgent Road Repair Request: Segment {segment.segment_id}"
            body = (
                f"Vehicle: {data.vehicle_id}\n"
                f"Segment: {segment.segment_id}\n"
                f"Damage Score: {segment.damage_score}\n"
                f"Severity: {segment_severity}\n"
                f"Action: Immediate Repair\n"
                f"Coordinates: {data.latitude}, {data.longitude}\n"
                f"Time: {datetime.utcnow().isoformat()}\n"
            )
            send_authority_report(subject, body)
            ok, resp = send_gov_report({
                "segment_id": segment.segment_id,
                "road_id": segment.road_id,
                "vehicle_id": data.vehicle_id,
                "damage_score": segment.damage_score,
                "severity": segment_severity,
                "action": "Immediate Repair"
            })
            log_event(db, "Complaints", "AutoGovAPI", f"segment={segment.segment_id}, success={ok}, resp={resp}")

    # Include simple prediction in response
    prediction = predict_segment_future_damage(db, segment_id, days=7)

    log_event(db, "Upload", data.vehicle_id, f"segment={segment_id}, damage_score={segment.damage_score}, severity={segment_severity}")

    log_event(db, "Upload", data.vehicle_id, f"segment={segment_id}, damage_score={segment.damage_score}, severity={segment_severity}")

    return {
        "status": "stored",
        "vehicle_id": data.vehicle_id,
        "route_id": active_route.id,
        "segment_id": segment_id,
        "damage_score": segment.damage_score,
        "segment_severity": segment_severity,
        "recommended_action": recommendation,
        "prediction": prediction,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/infer")
def infer_image(vehicle_id: str, file: UploadFile = File(...), auth=Depends(require_role(["vehicle", "admin", "manager"])), db: Session = Depends(get_db)):
    image_bytes = file.file.read()
    detections = infer_image_bytes(image_bytes)
    result = {"vehicle_id": vehicle_id, "detections": detections}
    log_event(db, "YOLO inference", vehicle_id, f"{len(detections)} detections")
    return result


@router.post("/infer/video")
def infer_video(vehicle_id: str, file: UploadFile = File(...), auth=Depends(require_role(["vehicle", "admin", "manager"])), db: Session = Depends(get_db)):
    import tempfile
    from ..utils.yolo_inference import annotate_video

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_in:
        tmp_in.write(file.file.read())
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace('.mp4', '_out.mp4')
    annotate_video(tmp_in_path, tmp_out_path)

    log_event(db, "YOLO video inference", vehicle_id, f"video processed: {tmp_out_path}")

    return {"vehicle_id": vehicle_id, "output_video_path": tmp_out_path, "status": "processed"}


@router.post("/train-yolo")
def train_yolo(
    data_dir: str = '/data/yolo',
    model_arch: str = 'yolov10n.pt',
    epochs: int = 80,
    imgsz: int = 640,
    auth=Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    results = train_yolo_model(data_dir, output_dir='runs/train', model_arch=model_arch, epochs=epochs, imgsz=imgsz)
    log_event(db, 'YOLO training', 'system', f'trained on {data_dir} model={model_arch}')
    return {'status': 'trained', 'results': str(results)}


@router.post("/eval-yolo")
def eval_yolo(
    weights_path: str = 'runs/train/road_damage/weights/best.pt',
    data_dir: str = '/data/yolo',
    auth=Depends(require_role(['admin'])),
    db: Session = Depends(get_db)
):
    metrics = evaluate_yolo_model(weights_path, data_dir)
    log_event(db, 'YOLO eval', 'system', f'weights={weights_path}')
    return {'status': 'evaluated', 'metrics': metrics}


@router.get("/segment/{segment_id}")
def get_segment(segment_id: str, db: Session = Depends(get_db)):
    segment = db.query(models.Segment).filter(models.Segment.segment_id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    segment_severity, recommendation = get_segment_status(segment.damage_score)
    return {
        "segment_id": segment.segment_id,
        "latitude": segment.latitude,
        "longitude": segment.longitude,
        "damage_score": segment.damage_score,
        "road_id": segment.road_id,
        "segment_severity": segment_severity,
        "recommended_action": recommendation
    }


@router.get("/predict/segment/{segment_id}")
def predict_segment(segment_id: str, db: Session = Depends(get_db)):
    segment = db.query(models.Segment).filter(models.Segment.segment_id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    prediction = predict_segment_future_damage(db, segment_id, days=7)
    # LSTM trend extension using history
    history = [d.damage_score for d in db.query(models.DamageData).filter(models.DamageData.latitude==segment.latitude, models.DamageData.longitude==segment.longitude).order_by(models.DamageData.timestamp.asc()).all()]
    lstm_prediction = None
    try:
        if len(history) >= 6:
            model, scaler = train_lstm_model(history)
            lstm_prediction = predict_lstm(model, scaler, history)
    except Exception:
        lstm_prediction = None

    if prediction is None:
        raise HTTPException(status_code=404, detail="Insufficient data for prediction")
    return {
        "segment_id": segment_id,
        "segment_damage_score": segment.damage_score,
        "prediction": prediction,
        "lstm_prediction": lstm_prediction
    }


@router.get("/routes/{vehicle_id}")
def get_vehicle_routes(vehicle_id: str, db: Session = Depends(get_db)):
    routes = db.query(models.Route).filter(models.Route.vehicle_id == vehicle_id).order_by(models.Route.start_time.desc()).all()
    return [{
        "route_id": r.id,
        "vehicle_id": r.vehicle_id,
        "start_time": r.start_time.isoformat(),
        "end_time": r.end_time.isoformat() if r.end_time else None
    } for r in routes]


@router.get("/route/{route_id}/points")
def get_route_points(route_id: int, db: Session = Depends(get_db)):
    points = db.query(models.RoutePoint).filter(models.RoutePoint.route_id == route_id).order_by(models.RoutePoint.timestamp.asc()).all()
    return [{
        "latitude": p.latitude,
        "longitude": p.longitude,
        "timestamp": p.timestamp.isoformat()
    } for p in points]


@router.post("/offline/sync")
def offline_sync(data_batch: List[schemas.VehicleData] = Body(...), auth=Depends(require_role(["vehicle", "admin", "manager"])), db: Session = Depends(get_db)):
    synced = 0
    errors = []

    for entry in data_batch:
        try:
            upload_data(entry, auth=auth, db=db)
            synced += 1
        except Exception as e:
            errors.append(str(e))

    return {"synced_records": synced, "errors": errors}


@router.get("/complaints")
def list_complaints(db: Session = Depends(get_db)):
    complaints = db.query(models.Complaint).order_by(models.Complaint.created_at.desc()).all()
    return [{
        "complaint_id": c.id,
        "segment_id": c.segment_id,
        "route_id": c.route_id,
        "vehicle_id": c.vehicle_id,
        "damage_score": c.damage_score,
        "priority": c.priority,
        "status": c.status,
        "created_at": c.created_at.isoformat(),
        "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        "remarks": c.remarks
    } for c in complaints]


@router.post("/complaints/{complaint_id}/send")
def send_complaint_report(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    subject = f"Road Complaint: Segment {complaint.segment_id}"
    body = (
        f"Route ID: {complaint.route_id}\n"
        f"Vehicle ID: {complaint.vehicle_id}\n"
        f"Segment ID: {complaint.segment_id}\n"
        f"Damage Score: {complaint.damage_score}\n"
        f"Priority: {complaint.priority}\n"
        f"Status: {complaint.status}\n"
        f"Remarks: {complaint.remarks}\n"
        f"Created at: {complaint.created_at.isoformat()}\n"
    )

    is_sent = send_authority_report(subject, body)
    if not is_sent:
        raise HTTPException(status_code=500, detail="Failed to send authority report")

    return {"status": "report_sent", "complaint_id": complaint.id}


@router.get("/complaints/{complaint_id}/pdf")
def complaint_pdf(complaint_id: int, db: Session = Depends(get_db), auth=Depends(require_role(['manager', 'admin']))):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    comp_data = {
        'complaint_id': complaint.id,
        'segment_id': complaint.segment_id,
        'route_id': complaint.route_id,
        'vehicle_id': complaint.vehicle_id,
        'damage_score': complaint.damage_score,
        'priority': complaint.priority,
        'status': complaint.status,
        'created_at': complaint.created_at.isoformat(),
        'resolved_at': complaint.resolved_at.isoformat() if complaint.resolved_at else None,
        'remarks': complaint.remarks
    }
    file_path = f"/tmp/complaint_{complaint_id}.pdf"
    generate_complaint_pdf(comp_data, file_path)
    return {"pdf_path": file_path, "status": "generated"}


@router.patch("/complaints/{complaint_id}")
def update_complaint(complaint_id: int, payload: schemas.ComplaintUpdate, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = payload.status
    complaint.remarks = payload.remarks
    if payload.status.lower() in ["resolved", "closed"]:
        complaint.resolved_at = datetime.utcnow()

    db.commit()
    return {"status": "updated", "complaint_id": complaint.id, "new_status": complaint.status}
