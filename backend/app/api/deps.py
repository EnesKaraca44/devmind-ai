from functools import lru_cache

from app.core.config import STORAGE_DIR
from app.infrastructure.storage import LocalStorage, Storage


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    """FastAPI bağımlılığı: endpoint'ler depolamayı BURADAN alır, kendileri oluşturmaz.
    Testlerde bu fonksiyon geçici klasörlü bir depolamayla DEĞİŞTİRİLEBİLİR."""
    return LocalStorage(STORAGE_DIR)
