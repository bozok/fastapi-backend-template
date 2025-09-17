from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

    response_data = response.json()

    # Check required fields
    assert "message" in response_data
    assert "status" in response_data
    assert "environment" in response_data
    assert "version" in response_data

    # Check specific values
    assert response_data["status"] == "healthy"
    assert response_data["version"] == "1.0.0"
    assert "Welcome to" in response_data["message"]

    # Environment should be one of the valid options
    assert response_data["environment"] in ["development", "staging", "production"]
