from fastapi import FastAPI
from .database import engine, Base
from .routes import vehicle, auth, audit

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart IoT Road Monitoring System")
app.include_router(auth.router)
app.include_router(vehicle.router)
app.include_router(audit.router)


@app.get("/")
def root():
    return {"message": "Smart IoT Road Monitoring System API is running"}
