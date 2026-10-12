from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.room_type import RoomType
from app.models.room import Room
from app.schemas.room_type import RoomTypeCreate, RoomTypePatch, RoomTypeUpdate


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


def get_room_types(db: Session) -> list[RoomType]:
    return db.query(RoomType).order_by(RoomType.id.asc()).all()


def get_room_type(db: Session, room_type_id: int) -> RoomType:
    room_type = db.get(RoomType, room_type_id)
    if room_type is None:
        raise ValueError("Room type not found")
    return room_type


def _apply_room_type_update(db: Session, room_type: RoomType, values: dict) -> RoomType:
    if "name" in values:
        duplicate = db.query(RoomType).filter(
            RoomType.name == values["name"], RoomType.id != room_type.id
        ).first()
        if duplicate:
            raise ValueError("Room type already exists")
    for key, value in values.items():
        setattr(room_type, key, value)
    try:
        db.commit()
        db.refresh(room_type)
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Room type already exists") from exc
    return room_type


def update_room_type(db: Session, room_type_id: int, data: RoomTypeUpdate) -> RoomType:
    room_type = get_room_type(db, room_type_id)
    return _apply_room_type_update(db, room_type, data.model_dump())


def patch_room_type(db: Session, room_type_id: int, data: RoomTypePatch) -> RoomType:
    room_type = get_room_type(db, room_type_id)
    return _apply_room_type_update(db, room_type, data.model_dump(exclude_unset=True))


def delete_room_type(db: Session, room_type_id: int) -> None:
    room_type = get_room_type(db, room_type_id)
    in_use = db.query(Room.id).filter(Room.room_type_id == room_type_id).first()
    if in_use:
        raise ValueError("Cannot delete a room type that is assigned to rooms")
    db.delete(room_type)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Cannot delete this room type because related records exist") from exc
