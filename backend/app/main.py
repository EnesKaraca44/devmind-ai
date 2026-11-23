from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import CORS_ORIGINS

app = FastAPI(title="DevMind AI API", version="0.1.0")

# CORS: tarayıcıya "şu adreslerden gelen sayfalar bana istek atabilir" der.
# "*" kullanmıyoruz: yalnızca bildiğimiz frontend adresine izin veriyoruz.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Tüm route'ları /api/v1 önekiyle takıyoruz: gelecekte v2 çıkarsa v1 bozulmaz.
app.include_router(health.router, prefix="/api/v1")
