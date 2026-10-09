from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.roles import Role
from app.models.user_role import UserRole


def assign_role(
    db: Session,
    user_id: int,
    role_name: str
):
    # Check that the role exists
    role = db.query(Role).filter(
        Role.name == role_name
    ).first()

    if role is None:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)

    # Prevent duplicate role assignment
    existing_user_role = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role.id
    ).first()

    if existing_user_role:
        raise ValueError("User already has this role")

    user_role = UserRole(
        user_id=user_id,
        role_id=role.id
    )

    db.add(user_role)

    try:
        db.commit()
        db.refresh(user_role)
    except IntegrityError:
        db.rollback()
        raise ValueError("Role assignment already exists")

    return user_role