from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_role, require_main_admin
from app.models.user import User
from app.models.roles import Role
from app.models.user_role import UserRole
from app.db.database import get_db
from app.schemas.user import AdminPasswordReset, AdminRoleAssignment, UserPatch, UserResponse, UserUpdate
from app.services.user_service import (
    delete_user, get_all_users, get_user, patch_user, reset_user_password, update_user,
)
from app.services.audit_service import create_audit_log


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


@router.get("/user-roles")
def list_user_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
) -> list[dict[str, str | int]]:
    result = []
    for user in get_all_users(db):
        names = {
            name for (name,) in db.query(Role.name).join(
                UserRole, Role.id == UserRole.role_id
            ).filter(UserRole.user_id == user.id).all()
        }
        if "ADMIN" in names:
            role_name = "ADMIN"
        elif names.intersection({"EMPLOYEE", "RECEPTIONIST"}):
            role_name = "EMPLOYEE"
        else:
            role_name = "USER"
        result.append({"user_id": user.id, "username": user.username, "role": role_name})
    return result


@router.put("/users/{user_id}/role")
def set_user_role(
    user_id: int,
    role_data: AdminRoleAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
    main_admin: User = Depends(require_main_admin),
) -> dict[str, str]:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.username == settings.MAIN_ADMIN_USERNAME:
        raise HTTPException(status_code=409, detail="The configured main administrator role cannot be changed here")

    role_rows = db.query(Role.name).join(
        UserRole, Role.id == UserRole.role_id
    ).filter(UserRole.user_id == target.id).all()
    old_names = {name for (name,) in role_rows}
    if "ADMIN" in old_names:
        raise HTTPException(status_code=409, detail="Administrator accounts cannot be changed to employee or user here")
    old_role = "EMPLOYEE" if old_names.intersection({"EMPLOYEE", "RECEPTIONIST"}) else "USER"
    if old_role == role_data.role:
        return {"message": f"{target.username} already has the {role_data.role} role"}

    try:
        desired_role = db.query(Role).filter(Role.name == role_data.role).first()
        if desired_role is None:
            desired_role = Role(name=role_data.role)
            db.add(desired_role)
            db.flush()

        managed_roles = db.query(UserRole).join(
            Role, Role.id == UserRole.role_id
        ).filter(
            UserRole.user_id == target.id,
            Role.name.in_(["USER", "CUSTOMER", "EMPLOYEE", "RECEPTIONIST"]),
        ).all()
        for assignment in managed_roles:
            db.delete(assignment)
        db.add(UserRole(user_id=target.id, role_id=desired_role.id))
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="ROLE_CHANGE",
            entity="User",
            entity_id=target.id,
            old_value=old_role,
            new_value=role_data.role,
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": f"{target.username} is now a {role_data.role.lower()}"}


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


@router.put("/users/{user_id}/password", status_code=204)
def reset_user_password_endpoint(
    user_id: int,
    password_data: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_main_admin),
) -> None:
    try:
        reset_user_password(db, user_id, current_user.id, password_data.password)
    except ValueError as exc:
        if str(exc) == "User not found":
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
