"""Create the configured main administrator when the API starts."""

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.roles import Role
from app.models.user import User
from app.models.user_role import UserRole

logger = logging.getLogger(__name__)


def bootstrap_main_admin(db: Session) -> bool:
    """Ensure the configured account has ADMIN access. Return whether it was created."""
    username = settings.MAIN_ADMIN_USERNAME
    user = db.query(User).filter(User.username == username).first()
    created = False

    if user is None:
        if not settings.MAIN_ADMIN_PASSWORD:
            logger.warning(
                "Main admin account '%s' was not created: set MAIN_ADMIN_PASSWORD "
                "(at least 12 characters) in .env, then restart the API.",
                username,
            )
            return False

        user = User(
            username=username,
            email=settings.MAIN_ADMIN_EMAIL,
            password_hash=hash_password(settings.MAIN_ADMIN_PASSWORD.get_secret_value()),
            full_name=settings.MAIN_ADMIN_FULL_NAME,
        )
        db.add(user)
        db.flush()
        created = True

    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if admin_role is None:
        admin_role = Role(name="ADMIN")
        db.add(admin_role)
        db.flush()

    assignment = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == admin_role.id,
    ).first()
    if assignment is None:
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    if created:
        logger.info("Created configured main administrator account '%s'.", username)
    return created
