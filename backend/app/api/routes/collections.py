import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import CollectionCreate, CollectionOut
from app.application import documents as use_cases
from app.infrastructure.database import get_session

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
def create_collection(body: CollectionCreate, session: Session = Depends(get_session)):
    return use_cases.create_collection(session, body.name, body.description)


@router.get("", response_model=list[CollectionOut])
def list_collections(session: Session = Depends(get_session)):
    return use_cases.list_collections(session)


@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(collection_id: uuid.UUID, session: Session = Depends(get_session)):
    try:
        return use_cases.get_collection(session, collection_id)
    except use_cases.CollectionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Koleksiyon bulunamadı.") from None
