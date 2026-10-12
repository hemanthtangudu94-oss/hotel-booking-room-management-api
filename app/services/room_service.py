from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.room_type import RoomType
from app.models.booking import Booking
from app.schemas.room import RoomCreate, RoomPatch, RoomUpdate

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


def get_room(db: Session, room_id: int) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise ValueError("Room not found")
    return room


def _apply_room_update(db: Session, room: Room, values: dict) -> Room:
    if "room_type_id" in values and db.get(RoomType, values["room_type_id"]) is None:
        raise ValueError("Room type not found")
    if "room_number" in values:
        duplicate = db.query(Room).filter(
            Room.room_number == values["room_number"], Room.id != room.id
        ).first()
        if duplicate:
            raise ValueError("Room number already exists")
    for key, value in values.items():
        setattr(room, key, value)
    try:
        db.commit()
        db.refresh(room)
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Room number already exists") from exc
    return room


def update_room(db: Session, room_id: int, room_data: RoomUpdate) -> Room:
    room = get_room(db, room_id)
    return _apply_room_update(db, room, room_data.model_dump())


def patch_room(db: Session, room_id: int, room_data: RoomPatch) -> Room:
    room = get_room(db, room_id)
    return _apply_room_update(db, room, room_data.model_dump(exclude_unset=True))


def delete_room(db: Session, room_id: int) -> None:
    room = get_room(db, room_id)
    has_booking_history = db.query(Booking.id).filter(
        Booking.room_id == room_id
    ).first()
    if has_booking_history:
        raise ValueError("Cannot delete a room with booking history")
    db.delete(room)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Cannot delete this room because related records exist") from exc
