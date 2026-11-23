from fastapi.testclient import TestClient

from app.main import app

# TestClient sunucuyu gerçekten başlatmadan, uygulamaya sahte HTTP isteği yollar.
client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "devmind-backend"}


def test_cors_allows_frontend_origin():
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_blocks_unknown_origin():
    response = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers


def test_unknown_route_returns_404():
    assert client.get("/api/v1/yok-boyle-bir-sey").status_code == 404
