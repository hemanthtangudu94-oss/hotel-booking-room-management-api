from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import create_booking, get_bookings, cancel_booking


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_booking_endpoint(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return create_booking(
            db,
            booking_data,
            current_user.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

@router.get(
    "/",
    response_model=list[BookingResponse]
)
def get_bookings_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_bookings(
        db,
        current_user.id,
        skip,
        limit
    )


@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingResponse
)
def cancel_booking_endpoint(
    booking_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return cancel_booking(
            db,
            booking_id,
            current_user.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    