import pytest
from httpx import AsyncClient

from backend.main import app


@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Smart IoT Road Monitoring System API is running"


@pytest.mark.anyio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/register", params={"username": "testuser", "password": "secret", "role": "vehicle"})
        assert r.status_code in (200, 201)
        assert r.json()["username"] == "testuser"

        r2 = await client.post("/auth/login", params={"username": "testuser", "password": "secret"})
        assert r2.status_code == 200
        data = r2.json()
        assert "access_token" in data
        assert data["role"] == "vehicle"


@pytest.mark.anyio
async def test_complaints_and_pdf_generation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register an admin user
        await client.post("/auth/register", params={"username": "admin_user", "password": "adminpass", "role": "admin"})
        admin_login = await client.post("/auth/login", params={"username": "admin_user", "password": "adminpass"})
        assert admin_login.status_code == 200
        token = admin_login.json()["access_token"]

        # List complaints must return 200 even if empty
        res = await client.get("/vehicle/complaints")
        assert res.status_code == 200

        # Request to generate complaint PDF for nonexistent id should be 404
        res_pdf = await client.get("/vehicle/complaints/9999/pdf", headers={"Authorization": f"Bearer {token}"})
        assert res_pdf.status_code == 404

