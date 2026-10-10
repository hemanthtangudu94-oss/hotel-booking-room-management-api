import logging

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.room import Room
from app.models.room_type import RoomType
from app.schemas.booking import BookingCreate
from app.services.audit_service import create_audit_log


logger = logging.getLogger(__name__)


def create_booking(
        db: Session,
        booking_data: BookingCreate,
        user_id: int
):
    #check whether room exists
    room = db.query(Room).filter(
        Room.id == booking_data.room_id
    ).first()

    if room is None:
        raise ValueError("Room not found")

    #checking room availability
    if room.status != "AVAILABLE":
        raise ValueError("Room is not available for booking")

    #validate dates
    if booking_data.check_out <= booking_data.check_in:
        raise ValueError("Check-out date must be after check-in date")

    #check room type
    room_type = db.query(RoomType).filter(
        RoomType.id == room.room_type_id
    ).first()

    if room_type is None:
        raise ValueError("Room type not found")

    #check overlapping booking
    overlapping_booking = db.query(Booking).filter(
        Booking.room_id == booking_data.room_id,
        Booking.status == "CONFIRMED",
        Booking.check_in < booking_data.check_out,
        Booking.check_out > booking_data.check_in
    ).first()

    if overlapping_booking:
        raise ValueError("Room is already booked for the selected dates")

    #calculate number of nights
    number_of_nights = (booking_data.check_out - booking_data.check_in).days

    #calculate total amount
    total_amount = Decimal(number_of_nights) * room_type.price_per_night

    #create booking
    booking = Booking(
        user_id=user_id,
        room_id=booking_data.room_id,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
        status="CONFIRMED",
        total_amount=total_amount
    )

    db.add(booking)

    try:
        db.flush()

        create_audit_log(
            db=db,
            user_id=user_id,
            action="CREATE",
            entity="Booking",
            entity_id=booking.id,
            new_value=f"Booking created for room { booking.room_id}",
            commit=False
        )
        db.commit()
        db.refresh(booking)

    except Exception:
        db.rollback()
        raise


    logger.info(
        "Booking created | user_id=%s | booking_id=%s | room_id=%s",
        user_id,
        booking.id,
        booking.room_id
    )

    return booking

def get_bookings(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int =10
):
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit <=0:
        raise ValueError("Limit must be greater than 0")
    
    if limit > 100:
        raise ValueError("Limit cannot exceed 100")
    
    bookings = db.query(Booking).filter(
        Booking.user_id == user_id
    ).order_by(
        Booking.created_at.desc()
    ).offset(skip).limit(limit).all()
 
    logger.info(
       "Bookings retrieved | user_id=%s | count=%s",
        user_id,
        len(bookings)
    )

    return bookings


def cancel_booking(
        db: Session,
        booking_id: int,
        user_id: int
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user_id
    ).first()

    if booking is None:
        raise ValueError("Booking not found")

    if booking.status != "CONFIRMED":
        raise ValueError("Booking cannot be cancelled")

    old_status = booking.status

    booking.status = "CANCELLED"
    
    try:

        db.flush()
        create_audit_log(
            db=db,
            user_id=user_id,
            action="CANCEL",
            entity="Booking",
            entity_id=booking.id,
            old_value=old_status,
            new_value="CANCELLED",
            commit=False
        )

        db.commit()
        db.refresh(booking)
    except Exception:
        db.rollback()
        raise


    logger.info(
        "Booking cancelled | user_id=%s | booking_id=%s",
        user_id,
        booking.id
    )

    return booking