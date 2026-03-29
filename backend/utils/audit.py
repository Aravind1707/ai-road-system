from .. import models


def log_event(db, event_type: str, source: str, details: str):
    entry = models.AuditLog(event_type=event_type, source=source, details=details)
    db.add(entry)
    db.commit()
