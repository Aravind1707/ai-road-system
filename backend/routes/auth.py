from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from .. import models
from ..routes.deps import get_db
from ..utils.security import get_password_hash, verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register_user(username: str, password: str, role: str = "vehicle", db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = models.User(username=username, hashed_password=get_password_hash(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"username": user.username, "role": user.role}


@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(subject=user.username, role=user.role)
    refresh_token = create_refresh_token(subject=user.username)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "role": user.role}


@router.post("/refresh")
def refresh_token(token: str, db: Session = Depends(get_db)):
    from ..utils.security import decode_token

    data = decode_token(token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = data.get("sub")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(subject=user.username, role=user.role)
    return {"access_token": new_access, "token_type": "bearer"}


def get_current_vehicle(authorization: str = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    provided_token = authorization.split("Bearer ")[1].strip()
    token = db.query(models.ApiToken).filter(models.ApiToken.token == provided_token, models.ApiToken.is_active == "true").first()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or inactive token")

    return token
