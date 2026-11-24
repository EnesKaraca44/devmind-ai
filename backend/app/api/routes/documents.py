import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_storage
from app.api.schemas import DocumentOut
from app.application import documents as use_cases
from app.core import config
from app.infrastructure.database import get_session
from app.infrastructure.storage import Storage
from app.ingestion.validation import FileTooLargeError, UploadValidationError

router = APIRouter(prefix="/documents", tags=["documents"])

_CHUNK = 1024 * 1024  # 1 MB'lık parçalar


async def _read_limited(file: UploadFile) -> bytes:
    """Dosyayı PARÇA PARÇA okur; sınırı aşar aşmaz bırakır (gerisini belleğe almaz)."""
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(_CHUNK):
        total += len(chunk)
        if total > config.MAX_UPLOAD_BYTES:
            limit_mb = config.MAX_UPLOAD_BYTES // (1024 * 1024)
            raise FileTooLargeError(f"Dosya çok büyük (en fazla {limit_mb} MB).")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload(
    collection_id: uuid.UUID = Form(),
    file: UploadFile = File(),
    session: Session = Depends(get_session),
    storage: Storage = Depends(get_storage),
):
    try:
        data = await _read_limited(file)
        # Not: upload_document eşzamanlı (senkron) çalışır; büyük PDF'ler isteği bekletebilir.
        # Arka plan işleri Sprint 9'da (md planı) ele alınacak.
        return use_cases.upload_document(session, storage, collection_id, file.filename or "", data)
    except FileTooLargeError as error:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(error)) from None
    except UploadValidationError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    except use_cases.CollectionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Koleksiyon bulunamadı.") from None
    except use_cases.DuplicateDocumentError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Bu dosya bu koleksiyona zaten yüklenmiş."
        ) from None


@router.get("", response_model=list[DocumentOut])
def list_documents(
    collection_id: uuid.UUID | None = None, session: Session = Depends(get_session)
):
    return use_cases.list_documents(session, collection_id)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, session: Session = Depends(get_session)):
    try:
        return use_cases.get_document(session, document_id)
    except use_cases.DocumentNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doküman bulunamadı.") from None


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    session: Session = Depends(get_session),
    storage: Storage = Depends(get_storage),
):
    try:
        use_cases.delete_document(session, storage, document_id)
    except use_cases.DocumentNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doküman bulunamadı.") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
