from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.room_type import RoomTypeCreate, RoomTypeResponse
from app.services.room_type_service import create_room_type

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