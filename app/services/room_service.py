from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.room_type import RoomType
from app.schemas.room import RoomCreate

def create_room(
    db: Session,
    room_data: RoomCreate
):
    # Check whether room type exists
    room_type = db.query(RoomType).filter(
        RoomType.id == room_data.room_type_id
    ).first()

    if room_type is None:
        raise ValueError("Room type not found")

    # Check for duplicate room number
    existing_room = db.query(Room).filter(
        Room.room_number == room_data.room_number
    ).first()

    if existing_room:
        raise ValueError("Room number already exists")

    # Validate floor
    if room_data.floor <= 0:
        raise ValueError("Floor must be greater than 0")

    # Create room
    room = Room(
        room_number=room_data.room_number,
        room_type_id=room_data.room_type_id,
        floor=room_data.floor,
        status=room_data.status
    )

    db.add(room)

    try:
        db.commit()
        db.refresh(room)
    except IntegrityError:
        db.rollback()
        raise ValueError("Room number already exists")

    return room

def get_rooms(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    room_status: str | None = None,
    sort_by: str = "room_number",
    sort_order: str = "asc"
):
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit <= 0:
        raise ValueError("Limit must be greater than 0")

    if limit > 100:
        raise ValueError("Limit cannot exceed 100")

    query = db.query(Room)

    # Filter by status
    if room_status:
        query = query.filter(Room.status == room_status)

    # Sorting
    sort_column = getattr(Room, sort_by, None)

    if sort_column is None:
        raise ValueError("Invalid sort field")

    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    elif sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        raise ValueError("Invalid sort order")

    # Pagination
    return query.offset(skip).limit(limit).all()