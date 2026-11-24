"""Uçtan uca API testleri: GERÇEK PostgreSQL + geçici klasör (tmp_path).

DATABASE_URL yoksa atlanır. Her test bir işlemde çalışıp sonunda geri alınır; diske yazılanlar
ise pytest'in geçici klasörüne gider (test bitince silinir).
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_storage
from app.application import documents as use_cases
from app.core import config
from app.infrastructure.database import get_engine, get_session
from app.infrastructure.models import Document
from app.infrastructure.storage import LocalStorage
from app.ingestion import validation
from app.main import app
from tests.pdf_factory import make_pdf

pytestmark = pytest.mark.skipif(not config.DATABASE_URL, reason="DATABASE_URL tanımlı değil")


@pytest.fixture
def session():
    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def storage_dir(tmp_path):
    root = tmp_path / "storage"
    return root


@pytest.fixture
def client(session, storage_dir):
    # Bağımlılık enjeksiyonu işe yarıyor: endpoint'ler gerçek oturum/depolama yerine bunları alır.
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_storage] = lambda: LocalStorage(storage_dir)
    yield TestClient(app)
    app.dependency_overrides.clear()


def stored_files(storage_dir):
    return sorted(p.name for p in storage_dir.iterdir()) if storage_dir.exists() else []


def new_collection(client, name="Deneme") -> str:
    response = client.post("/api/v1/collections", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def upload(client, collection_id, filename, data, content_type="application/octet-stream"):
    return client.post(
        "/api/v1/documents/upload",
        data={"collection_id": collection_id},
        files={"file": (filename, data, content_type)},
    )


# ---------- koleksiyonlar ----------


def test_collection_create_list_get(client):
    collection_id = new_collection(client, "Notlarım")

    assert client.get(f"/api/v1/collections/{collection_id}").json()["name"] == "Notlarım"
    assert collection_id in [c["id"] for c in client.get("/api/v1/collections").json()]


def test_unknown_collection_is_404_and_bad_uuid_is_422(client):
    assert client.get(f"/api/v1/collections/{uuid.uuid4()}").status_code == 404
    assert client.get("/api/v1/collections/bu-uuid-degil").status_code == 422


@pytest.mark.parametrize("body", [{"name": ""}, {}, {"name": "x" * 201}])
def test_collection_body_is_validated(client, body):
    assert client.post("/api/v1/collections", json=body).status_code == 422


# ---------- yükleme: başarılı yollar ----------


def test_upload_text_file(client, storage_dir):
    collection_id = new_collection(client)

    response = upload(client, collection_id, "not.txt", "merhaba dünya".encode("utf-8"))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["filename"] == "not.txt"
    assert body["mime_type"] == "text/plain"
    assert body["page_count"] is None
    assert "storage_key" not in body  # iç ayrıntı dışarı verilmez
    assert len(stored_files(storage_dir)) == 1


def test_upload_pdf_reports_page_count(client):
    collection_id = new_collection(client)
    pdf = make_pdf([[(72, 700, "Page one")], [(72, 700, "Page two")]])

    body = upload(client, collection_id, "rapor.pdf", pdf).json()

    assert body["status"] == "ready"
    assert body["page_count"] == 2
    assert body["mime_type"] == "application/pdf"


def test_unreadable_pdf_is_saved_as_failed_not_rejected(client, storage_dir):
    collection_id = new_collection(client)
    scanned_like = make_pdf([[], []])  # geçerli PDF ama içinde hiç yazı yok

    response = upload(client, collection_id, "taranmis.pdf", scanned_like)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert "OCR" in body["error_message"]
    assert len(stored_files(storage_dir)) == 1  # dosya tutuldu, kullanıcı sebebini görebilir


def test_path_traversal_filename_stays_inside_storage(client, storage_dir):
    collection_id = new_collection(client)

    response = upload(client, collection_id, "../../evil.txt", b"merhaba")

    assert response.status_code == 201
    assert response.json()["filename"] == "evil.txt"  # klasör kısımları atıldı
    assert not (storage_dir.parent / "evil.txt").exists()
    assert "evil" not in stored_files(storage_dir)[0]  # diskteki ad kullanıcıdan hiçbir şey içermez


# ---------- yükleme: reddedilen yollar (hiçbir şey kaydedilmemeli) ----------


def test_fake_pdf_is_rejected_with_400_and_nothing_is_stored(client, storage_dir, session):
    collection_id = new_collection(client)

    response = upload(client, collection_id, "sahte.pdf", b"bu aslinda duz metin")

    assert response.status_code == 400
    assert stored_files(storage_dir) == []
    assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_unsupported_extension_is_400(client, storage_dir):
    collection_id = new_collection(client)

    assert upload(client, collection_id, "virus.exe", b"MZ....").status_code == 400
    assert stored_files(storage_dir) == []


def test_too_large_file_is_413(client, storage_dir, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 10)
    monkeypatch.setattr(validation, "MAX_UPLOAD_BYTES", 10)
    collection_id = new_collection(client)

    response = upload(client, collection_id, "buyuk.txt", b"x" * 11)

    assert response.status_code == 413
    assert stored_files(storage_dir) == []


def test_unknown_collection_is_404_and_nothing_is_stored(client, storage_dir):
    response = upload(client, str(uuid.uuid4()), "not.txt", b"merhaba")

    assert response.status_code == 404
    assert stored_files(storage_dir) == []


def test_duplicate_in_same_collection_is_409_but_ok_in_another(client, storage_dir):
    first, second = new_collection(client, "A"), new_collection(client, "B")

    assert upload(client, first, "a.txt", b"ayni icerik").status_code == 201
    assert upload(client, first, "baska-ad.txt", b"ayni icerik").status_code == 409  # içerik aynı
    assert upload(client, second, "a.txt", b"ayni icerik").status_code == 201
    assert len(stored_files(storage_dir)) == 2  # 409 olan dosya diske yazılmadı


def test_missing_file_field_is_422(client):
    response = client.post("/api/v1/documents/upload", data={"collection_id": new_collection(client)})

    assert response.status_code == 422


# ---------- listeleme ve silme ----------


def test_list_documents_can_filter_by_collection(client):
    first, second = new_collection(client, "A"), new_collection(client, "B")
    upload(client, first, "a.txt", b"bir")
    upload(client, second, "b.txt", b"iki")

    assert len(client.get("/api/v1/documents").json()) == 2
    only_first = client.get("/api/v1/documents", params={"collection_id": first}).json()
    assert [d["filename"] for d in only_first] == ["a.txt"]


def test_delete_removes_record_and_file(client, storage_dir):
    collection_id = new_collection(client)
    document_id = upload(client, collection_id, "a.txt", b"merhaba").json()["id"]
    assert len(stored_files(storage_dir)) == 1

    assert client.delete(f"/api/v1/documents/{document_id}").status_code == 204

    assert client.get(f"/api/v1/documents/{document_id}").status_code == 404
    assert stored_files(storage_dir) == []
    assert client.delete(f"/api/v1/documents/{document_id}").status_code == 404  # ikinci silme


# ---------- hata yönetimi: veritabanı yazması başarısız olursa dosya geri silinir ----------


def test_file_is_cleaned_up_when_database_commit_fails(session, storage_dir, monkeypatch):
    collection = use_cases.create_collection(session, "Deneme", None)

    def broken_commit():
        raise RuntimeError("veritabani coktu")

    monkeypatch.setattr(session, "commit", broken_commit)

    with pytest.raises(RuntimeError):
        use_cases.upload_document(
            session, LocalStorage(storage_dir), collection.id, "a.txt", b"merhaba"
        )

    assert stored_files(storage_dir) == []  # yetim dosya kalmadı
