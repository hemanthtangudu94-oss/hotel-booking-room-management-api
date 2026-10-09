from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import oauth2_scheme
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

from app.models.roles import Role
from app.models.user_role import UserRole

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = db.get(User, int(user_id))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user

def require_role(required_role: str):
    def role_checker(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
    ):
        role = db.query(Role).join(
            UserRole,
            Role.id == UserRole.role_id
        ).filter(
            UserRole.user_id == current_user.id,
            Role.name == required_role
        ).first()

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return role_checker
