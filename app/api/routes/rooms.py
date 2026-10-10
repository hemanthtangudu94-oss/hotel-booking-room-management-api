from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.room import RoomCreate, RoomResponse
from app.services.room_service import create_room, get_rooms


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)


@router.post(
    "/",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED
)
def create_room_endpoint(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    try:
        return create_room(db, room_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

@router.get("/", response_model=list[RoomResponse])
def get_rooms_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    room_status: Literal["AVAILABLE", "MAINTENANCE", "CLEANING"] | None = None,
    sort_by: str = "room_number",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    try:
        return get_rooms(db, skip, limit, room_status, sort_by, sort_order)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
