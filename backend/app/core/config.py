import os

# Hangi web adreslerinin (origin) bu API'ye tarayıcıdan istek atmasına izin verilir.
# Virgülle ayrılmış liste; ortam değişkeniyle değiştirilebilir, varsayılan: Next.js dev sunucusu.
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
