from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check_returns_ok() -> None:
    """ The health endpoint should confirm that the API is responding."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}