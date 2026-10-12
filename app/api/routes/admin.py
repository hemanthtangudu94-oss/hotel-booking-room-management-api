from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role, require_main_admin
from app.models.user import User
from app.db.database import get_db
from app.schemas.user import UserPatch, UserResponse, UserUpdate
from app.services.user_service import (
    delete_user, get_all_users, get_user, patch_user, update_user,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/test")
def admin_test(
    current_user: User = Depends(require_role("ADMIN"))
) -> dict[str, str]:
    return{
        "message": "Admin access granted",
        "username": current_user.username
    }

@router.get("/users", response_model=list[UserResponse])
def list_all_users(
    db:Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
) -> list[UserResponse]:
    return get_all_users(db)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
) -> UserResponse:
    try:
        return get_user(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.delete("/users/{user_id}", status_code=204)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_main_admin)
) -> None:
    try:
        delete_user(db, user_id)
    except ValueError as e:
        if str(e) == "User not found":
            raise HTTPException(
                status_code=404,
                detail=str(e)
            ) from e

        raise HTTPException(
            status_code=409,
            detail=str(e)
        ) from e


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_main_admin)
) -> UserResponse:
    try:
        return update_user(db, user_id, user_data)

    except ValueError as e:
        if str(e) == "User not found":
            raise HTTPException(
                status_code=404,
                detail=str(e)
            ) from e

        raise HTTPException(
            status_code=409,
            detail=str(e)
        ) from e


@router.patch("/users/{user_id}", response_model=UserResponse)
def patch_user_endpoint(
    user_id: int,
    user_data: UserPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_main_admin),
) -> UserResponse:
    try:
        return patch_user(db, user_id, user_data)
    except ValueError as exc:
        message = str(exc)
        code = 404 if message == "User not found" else 409
        raise HTTPException(status_code=code, detail=message) from exc
