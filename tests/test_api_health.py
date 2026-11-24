from fastapi.testclient import TestClient

from study_buddy.api.main import app

client = TestClient(app)


def test_health_returns_200():
    # goes through main.py, so this also fails if the router isn't included
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
