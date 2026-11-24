import os

# Yüklenebilecek en büyük dosya (byte). Varsayılan 20 MB; MAX_UPLOAD_BYTES ile değiştirilir.
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))

# Hangi web adreslerinin (origin) bu API'ye tarayıcıdan istek atmasına izin verilir.
# Virgülle ayrılmış liste; ortam değişkeniyle değiştirilebilir, varsayılan: Next.js dev sunucusu.
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
