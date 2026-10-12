from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.room import RoomCreate, RoomPatch, RoomResponse, RoomUpdate
from app.services.room_service import (
    create_room, delete_room, get_room, get_rooms, patch_room, update_room,
)


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


@router.get("/{room_id}", response_model=RoomResponse)
def get_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        return get_room(db, room_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{room_id}", response_model=RoomResponse)
def update_room_endpoint(
    room_id: int,
    room_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        return update_room(db, room_id, room_data)
    except ValueError as exc:
        message = str(exc)
        code = 404 if message == "Room not found" else 400 if message == "Room type not found" else 409
        raise HTTPException(status_code=code, detail=message) from exc


@router.patch("/{room_id}", response_model=RoomResponse)
def patch_room_endpoint(
    room_id: int,
    room_data: RoomPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        return patch_room(db, room_id, room_data)
    except ValueError as exc:
        message = str(exc)
        code = 404 if message == "Room not found" else 400 if message == "Room type not found" else 409
        raise HTTPException(status_code=code, detail=message) from exc


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_endpoint(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        delete_room(db, room_id)
    except ValueError as exc:
        message = str(exc)
        code = 404 if message == "Room not found" else 409
        raise HTTPException(status_code=code, detail=message) from exc
