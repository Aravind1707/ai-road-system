from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt

from ..database import SessionLocal
from .. import models
from ..config import JWT_SECRET_KEY, JWT_ALGORITHM


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.split("Bearer ")[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    role = payload.get("role")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"user": user, "role": role}


def require_role(required_roles: list):
    def _require_role(current=Depends(get_current_user)):
        if current["role"] not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current

    return _require_role
