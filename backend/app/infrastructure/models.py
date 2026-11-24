import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base

DOCUMENT_STATUSES = ("pending", "processing", "ready", "failed")


class Collection(Base):
    """Dokümanları gruplayan klasör gibi bir kavram.

    NOT: md şemasında collections.user_id de var. Kimlik doğrulama Sprint 9'da gelecek;
    user_id'yi o zaman migration ile EKLEYECEĞİZ. Sprint 5'ten (RAG) önce eklenmeli,
    çünkü kullanıcılar arası veri izolasyonu ona bağlı.
    """

    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # passive_deletes: koleksiyon silinince dokümanları Python tek tek silmesin,
    # veritabanındaki ON DELETE CASCADE kuralı halletsin (daha hızlı ve tutarlı).
    documents: Mapped[list["Document"]] = relationship(
        back_populates="collection", passive_deletes=True
    )


class Document(Base):
    """Yüklenen bir dosyanın BİLGİ KARTI. Dosyanın içeriği burada değil, storage'da durur."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'ready', 'failed')", name="status"
        ),
        # Aynı koleksiyona aynı içerik (aynı checksum) iki kez eklenemesin.
        # Açık ad veriyoruz: otomatik ad yalnızca ilk sütunu içerip yanıltıcı olurdu.
        UniqueConstraint("collection_id", "checksum", name="uq_documents_collection_id_checksum"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE")
    )
    filename: Mapped[str] = mapped_column(String(255))  # temizlenmiş orijinal ad (etiket)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)  # diskteki rastgele ad
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum: Mapped[str] = mapped_column(String(64))  # SHA-256 hex
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    collection: Mapped[Collection] = relationship(back_populates="documents")
