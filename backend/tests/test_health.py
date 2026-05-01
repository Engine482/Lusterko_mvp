from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_success_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"success": True, "data": {"status": "ok"}}
