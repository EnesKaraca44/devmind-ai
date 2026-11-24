"""Entegrasyon testleri: GERÇEK PostgreSQL'e karşı çalışır.

Çalıştırmak için önce DATABASE_URL gerekir (PowerShell: `. .\\scripts\\dev-env.ps1`).
Yoksa bu testler atlanır (skip); böylece veritabanı olmayan ortamda (ör. CI'ın ilk hâli) bozulmaz.
Her test bir işlem (transaction) içinde çalışır ve sonunda GERİ ALINIR: veritabanında veri kalmaz.
"""

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import DATABASE_URL
from app.infrastructure.database import get_engine
from app.infrastructure.models import Collection, Document

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL tanımlı değil")


@pytest.fixture
def session():
    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    # create_savepoint: test içinde commit/rollback olsa bile dıştaki işlem bizde kalır.
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()  # test verisini sil
        connection.close()
        engine.dispose()


def make_document(collection_id, *, checksum="a" * 64, storage_key=None, **overrides):
    return Document(
        collection_id=collection_id,
        filename="not.txt",
        storage_key=storage_key or f"{uuid.uuid4().hex}.txt",
        mime_type="text/plain",
        file_size=12,
        checksum=checksum,
        **overrides,
    )


def make_collection(session) -> Collection:
    collection = Collection(name="Deneme")
    session.add(collection)
    session.flush()
    return collection


def test_defaults_are_filled_by_database(session):
    collection = make_collection(session)
    document = make_document(collection.id)
    session.add(document)
    session.flush()
    session.refresh(document)

    assert isinstance(document.id, uuid.UUID)
    assert document.status == "pending"
    assert document.created_at is not None and document.updated_at is not None
    assert document.error_message is None and document.page_count is None


def test_invalid_status_is_rejected(session):
    collection = make_collection(session)
    session.add(make_document(collection.id, status="bilinmeyen"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_document_needs_an_existing_collection(session):
    session.add(make_document(uuid.uuid4()))  # böyle bir koleksiyon yok

    with pytest.raises(IntegrityError):
        session.flush()


def test_same_checksum_twice_in_one_collection_is_rejected(session):
    collection = make_collection(session)
    session.add(make_document(collection.id, checksum="b" * 64))
    session.flush()
    session.add(make_document(collection.id, checksum="b" * 64))

    with pytest.raises(IntegrityError):
        session.flush()


def test_same_checksum_in_different_collections_is_allowed(session):
    first, second = make_collection(session), make_collection(session)
    session.add_all(
        [
            make_document(first.id, checksum="c" * 64),
            make_document(second.id, checksum="c" * 64),
        ]
    )

    session.flush()  # hata fırlatmamalı


def test_storage_key_must_be_unique(session):
    first, second = make_collection(session), make_collection(session)
    session.add(make_document(first.id, checksum="d" * 64, storage_key="ayni.txt"))
    session.flush()
    session.add(make_document(second.id, checksum="e" * 64, storage_key="ayni.txt"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_collection_deletes_its_documents(session):
    collection = make_collection(session)
    session.add_all(
        [
            make_document(collection.id, checksum="1" * 64),
            make_document(collection.id, checksum="2" * 64),
        ]
    )
    session.flush()
    count = select(func.count()).select_from(Document).where(Document.collection_id == collection.id)
    assert session.scalar(count) == 2

    session.delete(collection)
    session.flush()

    assert session.scalar(count) == 0  # ON DELETE CASCADE çalıştı
