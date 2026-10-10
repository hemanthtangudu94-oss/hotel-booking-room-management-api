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
    allowed_sort_fields = {
        "room_number": Room.room_number,
        "floor": Room.floor,
        "status": Room.status,
        "room_type_id": Room.room_type_id,
    }

    sort_column = allowed_sort_fields.get(sort_by)

    if sort_column is None:
        raise ValueError("Invalid sort field. Allowed fields: "
                         "room_number, floor, status, room_type_id")

    normalized_sort_order = sort_order.lower()

    if normalized_sort_order == "desc":
        query = query.order_by(sort_column.desc())
    elif normalized_sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        raise ValueError(
            "Invalid sort order. Allowed values: asc, desc"
        )

    # Pagination
    return query.offset(skip).limit(limit).all()