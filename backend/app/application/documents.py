"""Doküman kullanım senaryoları (use case'ler): "bir dosya yüklenince ne olur?"

Bu katman web'i (FastAPI) bilmez: girdi alır, iş kurallarını uygular, sonuç ya da hata döner.
Aynı mantığı ileride başka bir arayüzden (CLI, MCP) de çağırabiliriz.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.models import Collection, Document
from app.infrastructure.storage import Storage
from app.ingestion.parsers.base import Parser, ParserError
from app.ingestion.parsers.pdf import PdfParser
from app.ingestion.parsers.text import TextParser
from app.ingestion.validation import validate_upload

# Uzantıya göre hangi parser, hangi MIME türü.
_PARSERS: dict[str, Parser] = {".pdf": PdfParser(), ".txt": TextParser(), ".md": TextParser()}
_MIME_TYPES = {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/markdown"}


class CollectionNotFoundError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class DuplicateDocumentError(Exception):
    """Aynı içerik (checksum) aynı koleksiyona zaten yüklenmiş."""


def create_collection(session: Session, name: str, description: str | None) -> Collection:
    collection = Collection(name=name.strip(), description=description)
    session.add(collection)
    session.commit()
    return collection


def list_collections(session: Session) -> list[Collection]:
    return list(session.scalars(select(Collection).order_by(Collection.created_at.desc())))


def get_collection(session: Session, collection_id: uuid.UUID) -> Collection:
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise CollectionNotFoundError
    return collection


def upload_document(
    session: Session,
    storage: Storage,
    collection_id: uuid.UUID,
    raw_filename: str,
    data: bytes,
) -> Document:
    # 1) Güvenlik görevlisi: ad, uzantı, boyut, içerik (hata verirse burada biter, hiçbir şey kaydedilmez)
    upload = validate_upload(raw_filename, data)

    # 2) Koleksiyon var mı?
    get_collection(session, collection_id)

    # 3) Aynı içerik bu koleksiyonda zaten var mı?
    already = session.scalar(
        select(Document.id).where(
            Document.collection_id == collection_id, Document.checksum == upload.checksum
        )
    )
    if already is not None:
        raise DuplicateDocumentError

    # 4) Okuyabiliyor muyuz? Okunamayan dosya reddedilmez, "failed" olarak kaydedilir:
    #    kullanıcı listede "şu dosya okunamadı, sebebi bu" görebilsin.
    status, error_message, page_count = "ready", None, None
    try:
        parsed = _PARSERS[upload.extension].parse(data)
        page_count = len(parsed.pages) if parsed.pages is not None else None
    except ParserError as error:
        status, error_message = "failed", str(error)

    # 5) Önce dosyayı yaz, sonra kaydı ekle. Kayıt başarısız olursa dosyayı geri sil:
    #    "kaydı olmayan yetim dosya" bırakmayız.
    storage.save(upload.storage_name, data)
    document = Document(
        collection_id=collection_id,
        filename=upload.display_name,
        storage_key=upload.storage_name,
        mime_type=_MIME_TYPES[upload.extension],
        file_size=upload.size,
        checksum=upload.checksum,
        status=status,
        error_message=error_message,
        page_count=page_count,
    )
    session.add(document)
    try:
        session.commit()
    except IntegrityError:
        # İki kullanıcı aynı anda aynı dosyayı yüklediyse 3. adımdaki kontrol ikisinden de geçer;
        # veritabanındaki UNIQUE kısıtı son savunma hattıdır.
        session.rollback()
        storage.delete(upload.storage_name)
        raise DuplicateDocumentError from None
    except Exception:
        session.rollback()
        storage.delete(upload.storage_name)
        raise
    return document


def list_documents(session: Session, collection_id: uuid.UUID | None = None) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc())
    if collection_id is not None:
        query = query.where(Document.collection_id == collection_id)
    return list(session.scalars(query))


def get_document(session: Session, document_id: uuid.UUID) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise DocumentNotFoundError
    return document


def delete_document(session: Session, storage: Storage, document_id: uuid.UUID) -> None:
    document = get_document(session, document_id)
    storage_key = document.storage_key
    # Önce veritabanı: dosya silinemezse en kötü ihtimalle yetim bir dosya kalır (zararsız).
    # Ters sırada kayıt kalıp dosya gitseydi, kullanıcı var olmayan bir dosyayı listede görürdü.
    session.delete(document)
    session.commit()
    storage.delete(storage_key)
