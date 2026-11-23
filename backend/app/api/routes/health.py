from fastapi import APIRouter
from pydantic import BaseModel

# Router: ilgili endpoint'leri gruplayan küçük bir "alt uygulama".
# main.py bunu ana uygulamaya takar.
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Cevabın şekli. FastAPI bunu doğrular ve /docs sayfasına otomatik yazar."""

    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Veritabanına bağlanmıyoruz: bu endpoint sadece "sunucu ayakta mı?" sorusunu yanıtlar.
    return HealthResponse(status="ok", service="devmind-backend")
