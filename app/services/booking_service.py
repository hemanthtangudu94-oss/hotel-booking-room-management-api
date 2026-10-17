import logging

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.room import Room
from app.models.room_type import RoomType
from app.models.payments import Payment
from app.schemas.booking import BookingCreate, BookingPatch, BookingUpdate
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
        user_id: int | None,
        skip: int = 0,
        limit: int =10
):
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit <=0:
        raise ValueError("Limit must be greater than 0")
    
    if limit > 100:
        raise ValueError("Limit cannot exceed 100")
    
    query = db.query(Booking)
    if user_id is not None:
        query = query.filter(Booking.user_id == user_id)
    bookings = query.order_by(
        Booking.created_at.desc()
    ).offset(skip).limit(limit).all()
 
    logger.info(
       "Bookings retrieved | user_id=%s | count=%s",
        user_id,
        len(bookings)
    )

    return bookings


def get_booking(db: Session, booking_id: int, user_id: int | None) -> Booking:
    query = db.query(Booking).filter(Booking.id == booking_id)
    if user_id is not None:
        query = query.filter(Booking.user_id == user_id)
    booking = query.first()
    if booking is None:
        raise ValueError("Booking not found")
    return booking


def update_booking(
    db: Session,
    booking_id: int,
    user_id: int | None,
    booking_data: BookingUpdate | BookingPatch,
    actor_id: int | None = None,
) -> Booking:
    booking = get_booking(db, booking_id, user_id)
    if booking.status != "CONFIRMED":
        raise ValueError("Booking cannot be updated")
    if db.query(Payment.id).filter(
        Payment.booking_id == booking_id, Payment.status == "PAID"
    ).first():
        raise ValueError("A paid booking cannot be updated")

    values = booking_data.model_dump(exclude_unset=True)
    room_id = values.get("room_id", booking.room_id)
    check_in = values.get("check_in", booking.check_in)
    check_out = values.get("check_out", booking.check_out)
    if check_out <= check_in:
        raise ValueError("Check-out date must be after check-in date")

    room = db.get(Room, room_id)
    if room is None:
        raise ValueError("Room not found")
    if room.status != "AVAILABLE":
        raise ValueError("Room is not available for booking")
    overlap = db.query(Booking.id).filter(
        Booking.room_id == room_id,
        Booking.id != booking_id,
        Booking.status == "CONFIRMED",
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    ).first()
    if overlap:
        raise ValueError("Room is already booked for the selected dates")
    room_type = db.get(RoomType, room.room_type_id)
    if room_type is None:
        raise ValueError("Room type not found")

    old_value = (
        f"Room: {booking.room_id}, Check-in: {booking.check_in}, "
        f"Check-out: {booking.check_out}, Total: {booking.total_amount}"
    )
    booking.room_id = room_id
    booking.check_in = check_in
    booking.check_out = check_out
    booking.total_amount = Decimal((check_out - check_in).days) * room_type.price_per_night
    new_value = (
        f"Room: {booking.room_id}, Check-in: {booking.check_in}, "
        f"Check-out: {booking.check_out}, Total: {booking.total_amount}"
    )
    try:
        db.flush()
        create_audit_log(
            db=db, user_id=actor_id if actor_id is not None else user_id, action="UPDATE", entity="Booking",
            entity_id=booking.id, old_value=old_value, new_value=new_value,
            commit=False,
        )
        db.commit()
        db.refresh(booking)
    except Exception:
        db.rollback()
        raise
    return booking


def cancel_booking(
        db: Session,
        booking_id: int,
        user_id: int | None,
        actor_id: int | None = None,
):
    booking = get_booking(db, booking_id, user_id)

    if booking.status != "CONFIRMED":
        raise ValueError("Booking cannot be cancelled")

    old_status = booking.status

    booking.status = "CANCELLED"
    
    try:

        db.flush()
        create_audit_log(
            db=db,
            user_id=actor_id if actor_id is not None else user_id,
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
