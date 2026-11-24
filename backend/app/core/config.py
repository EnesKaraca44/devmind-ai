import os

# Yüklenebilecek en büyük dosya (byte). Varsayılan 20 MB; MAX_UPLOAD_BYTES ile değiştirilir.
MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))

# Veritabanı bağlantı adresi. Parola içerdiği için KODA YAZILMAZ; ortam değişkeninden gelir.
# Konteyner içinden:      postgresql+psycopg://KULLANICI:PAROLA@db:5432/ad        (servis adı "db")
# Kendi bilgisayarından:  postgresql+psycopg://KULLANICI:PAROLA@127.0.0.1:5433/ad (yayınlanan port;
#                         "localhost" değil: IPv6 (::1) denemesi saniyelerce takılır)
DATABASE_URL: str | None = os.getenv("DATABASE_URL")

# Hangi web adreslerinin (origin) bu API'ye tarayıcıdan istek atmasına izin verilir.
# Virgülle ayrılmış liste; ortam değişkeniyle değiştirilebilir, varsayılan: Next.js dev sunucusu.
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
