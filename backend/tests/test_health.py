from fastapi.testclient import TestClient

from app.main import app

# TestClient sunucuyu gerçekten başlatmadan, uygulamaya sahte HTTP isteği yollar.
client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "devmind-backend"}


def test_unknown_route_returns_404():
    assert client.get("/api/v1/yok-boyle-bir-sey").status_code == 404
