from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import get_audit_logs

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)

@router.get(
    "/",
    response_model=list[AuditLogResponse]
)
def get_audit_logs_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    return get_audit_logs(
        db,
        skip,
        limit
    )