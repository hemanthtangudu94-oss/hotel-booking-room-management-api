from fastapi import APIRouter, Depends

from app.core.dependencies import require_role
from app.models.user import User

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