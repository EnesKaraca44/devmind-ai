from fastapi import FastAPI

from app.api.routes import health

app = FastAPI(title="DevMind AI API", version="0.1.0")

# Tüm route'ları /api/v1 önekiyle takıyoruz: gelecekte v2 çıkarsa v1 bozulmaz.
app.include_router(health.router, prefix="/api/v1")
