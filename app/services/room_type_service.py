from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.room_type import RoomType
from app.schemas.room_type import RoomTypeCreate


def create_room_type(
    db: Session,
    room_type_data: RoomTypeCreate
):
    # Business validation
    if room_type_data.capacity <= 0:
        raise ValueError("Capacity must be greater than 0")

    if room_type_data.price_per_night <= 0:
        raise ValueError("Price per night must be greater than 0")

    # Check for duplicate room type
    existing_room_type = db.query(RoomType).filter(
        RoomType.name == room_type_data.name
    ).first()

    if existing_room_type:
        raise ValueError("Room type already exists")

    # Create room type
    room_type = RoomType(
        name=room_type_data.name,
        description=room_type_data.description,
        capacity=room_type_data.capacity,
        price_per_night=room_type_data.price_per_night
    )

    db.add(room_type)

    try:
        db.commit()
        db.refresh(room_type)
    except IntegrityError:
        db.rollback()
        raise ValueError("Room type already exists")

    return room_type