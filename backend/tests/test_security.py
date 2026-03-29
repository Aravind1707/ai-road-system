import pytest
from httpx import AsyncClient
from backend.main import app


@pytest.mark.anyio
async def test_jwt_protected_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # register user
        await client.post("/auth/register", params={"username": "secuser", "password": "secret", "role": "vehicle"})
        login_res = await client.post("/auth/login", params={"username": "secuser", "password": "secret"})
        token = login_res.json()["access_token"]

        # protected endpoint without token should fail
        r0 = await client.post("/vehicle/upload", json={"vehicle_id": "sec1", "latitude": 13.0, "longitude": 80.0, "severity": "Low", "length": 5.0, "damage_type": "crack", "vibration": 0.1, "speed": 20.0})
        assert r0.status_code == 401

        # with token should succeed
        r1 = await client.post(
            "/vehicle/upload",
            json={"vehicle_id": "sec1", "latitude": 13.0, "longitude": 80.0, "severity": "Low", "length": 5.0, "damage_type": "crack", "vibration": 0.1, "speed": 20.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert r1.status_code == 200
