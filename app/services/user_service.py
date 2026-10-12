from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.user_role import UserRole
from app.models.booking import Booking
from app.schemas.user import UserCreate, UserPatch, UserUpdate


def create_user(db: Session, user_data: UserCreate) -> User:
    # Check duplicate username
    existing_username = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if existing_username:
        raise ValueError("Username already exists")

    # Check duplicate email
    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_email:
        raise ValueError("Email already exists")

    hashed_password = hash_password(user_data.password)

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise ValueError("Username or email already exists")

    return user


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id.asc()).all()


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    return user



def delete_user(db: Session, user_id: int) -> None:
    user = db.get(User, user_id)

    if user is None:
        raise ValueError("User not found")

    existing_booking = db.query(Booking.id).filter(
        Booking.user_id == user_id
    ).first()

    if existing_booking:
        raise ValueError(
            "Cannot delete a user who has booking history"
        )

    try:
        db.query(UserRole).filter(
            UserRole.user_id == user_id
        ).delete(synchronize_session=False)

        db.delete(user)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Cannot delete this user because related records exist"
        )

def update_user(
        db: Session,
        user_id: int,
        user_data: UserUpdate
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise ValueError("User not found")

    return _apply_user_update(db, user, user_data.model_dump())


def patch_user(db: Session, user_id: int, user_data: UserPatch) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    return _apply_user_update(db, user, user_data.model_dump(exclude_unset=True))


def _apply_user_update(db: Session, user: User, values: dict) -> User:
    for field in ("username", "email"):
        if field in values:
            duplicate = db.query(User).filter(
                getattr(User, field) == values[field], User.id != user.id
            ).first()
            if duplicate:
                raise ValueError(f"{field.capitalize()} already exists")

    for field, value in values.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Username or email already exists") from e

    return user
