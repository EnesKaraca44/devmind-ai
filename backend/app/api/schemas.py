import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollectionCreate(BaseModel):
    """İstek gövdesi: Pydantic gelen veriyi doğrular (boş ad, aşırı uzun ad reddedilir)."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class CollectionOut(BaseModel):
    # from_attributes: veritabanı nesnesinden (Collection) doğrudan okuyabilsin.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime


class DocumentOut(BaseModel):
    """Dışarı verdiğimiz doküman bilgisi. storage_key'i BİLEREK vermiyoruz:
    iç ayrıntı (diskteki ad), kullanıcının görmesine gerek yok."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    collection_id: uuid.UUID
    filename: str
    mime_type: str
    file_size: int
    checksum: str
    status: str
    error_message: str | None
    page_count: int | None
    created_at: datetime
