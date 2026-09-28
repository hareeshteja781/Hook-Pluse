import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.endpoint import Endpoint
from app.models.user import User
from app.schemas.endpoint import EndpointCreate, EndpointCreated, EndpointRead

router = APIRouter(prefix="/endpoints", tags=["endpoints"])

@router.post("", response_model=EndpointCreated, status_code=status.HTTP_201_CREATED)
def create_endpoint(payload: EndpointCreate, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> Endpoint:
    endpoint = Endpoint(owner_id=current_user.id, name=payload.name, target_url=str(payload.target_url), signing_secret=secrets.token_urlsafe(32))
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint

@router.get("", response_model=list[EndpointRead])
def list_endpoints(db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> list[Endpoint]:
    return list(db.scalars(select(Endpoint).where(Endpoint.owner_id == current_user.id).order_by(Endpoint.created_at.desc())))

@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(endpoint_id: str, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> None:
    endpoint = db.scalar(select(Endpoint).where(Endpoint.id == endpoint_id, Endpoint.owner_id == current_user.id))
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    db.delete(endpoint)
    db.commit()
