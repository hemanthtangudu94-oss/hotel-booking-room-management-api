from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingPatch, BookingResponse, BookingUpdate
from app.services.booking_service import (
    cancel_booking, create_booking, get_booking, get_bookings, update_booking,
)


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


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking_endpoint(
    booking_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_booking(db, booking_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _booking_update_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    code = 404 if message in {"Booking not found", "Room not found", "Room type not found"} else 409
    return HTTPException(status_code=code, detail=message)


@router.put("/{booking_id}", response_model=BookingResponse)
def replace_booking_endpoint(
    booking_id: int,
    booking_data: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_booking(db, booking_id, current_user.id, booking_data)
    except ValueError as exc:
        raise _booking_update_error(exc) from exc


@router.patch("/{booking_id}", response_model=BookingResponse)
def patch_booking_endpoint(
    booking_id: int,
    booking_data: BookingPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_booking(db, booking_id, current_user.id, booking_data)
    except ValueError as exc:
        raise _booking_update_error(exc) from exc


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


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking_endpoint(
    booking_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cancel_booking(db, booking_id, current_user.id)
    except ValueError as exc:
        message = str(exc)
        code = 404 if message == "Booking not found" else 409
        raise HTTPException(status_code=code, detail=message) from exc

