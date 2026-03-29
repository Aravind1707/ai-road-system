from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..routes.deps import get_db, require_role
from .. import models

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/")
def list_audit_logs(status: str = None, source: str = None, event_type: str = None, db: Session = Depends(get_db), auth=Depends(require_role(["admin", "manager"]))):
    query = db.query(models.AuditLog)
    if status:
        query = query.filter(models.AuditLog.details.ilike(f"%{status}%"))
    if source:
        query = query.filter(models.AuditLog.source == source)
    if event_type:
        query = query.filter(models.AuditLog.event_type == event_type)
    logs = query.order_by(models.AuditLog.created_at.desc()).all()
    return [{
        "id": l.id,
        "event_type": l.event_type,
        "source": l.source,
        "details": l.details,
        "created_at": l.created_at.isoformat()
    } for l in logs]
