from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.room_type import (
    RoomTypeCreate, RoomTypePatch, RoomTypeResponse, RoomTypeUpdate,
)
from app.services.room_type_service import (
    create_room_type, delete_room_type, get_room_type, get_room_types,
    patch_room_type, update_room_type,
)

router = APIRouter(
    prefix="/room-types",
    tags=["Room Types"]
)


@router.post(
    "/",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_201_CREATED
)

def create_room_type_endpoint(
    room_type_data: RoomTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    try:
        return create_room_type(db, room_type_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=list[RoomTypeResponse])
def list_room_types_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    return get_room_types(db)


@router.get("/{room_type_id}", response_model=RoomTypeResponse)
def get_room_type_endpoint(
    room_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        return get_room_type(db, room_type_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _room_type_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    code = 404 if message == "Room type not found" else 409
    return HTTPException(status_code=code, detail=message)


@router.put("/{room_type_id}", response_model=RoomTypeResponse)
def update_room_type_endpoint(
    room_type_id: int,
    room_type_data: RoomTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        return update_room_type(db, room_type_id, room_type_data)
    except ValueError as exc:
        raise _room_type_error(exc) from exc


@router.patch("/{room_type_id}", response_model=RoomTypeResponse)
def patch_room_type_endpoint(
    room_type_id: int,
    room_type_data: RoomTypePatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        return patch_room_type(db, room_type_id, room_type_data)
    except ValueError as exc:
        raise _room_type_error(exc) from exc


@router.delete("/{room_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_type_endpoint(
    room_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    try:
        delete_room_type(db, room_type_id)
    except ValueError as exc:
        raise _room_type_error(exc) from exc
