import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

def create_audit_log(
    db: Session,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int,
    old_value: str | None = None,
    new_value: str | None = None,
    commit: bool = True
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value
    )

    db.add(audit_log)
    
    try:
        if commit:
            db.commit()
            db.refresh(audit_log)
        else:
            db.flush()

    except IntegrityError:
        if commit:
            db.rollback()
        raise ValueError("Unable to create audit log")    

    logger.info(
        "Audit log created | user_id=%s | action=%s | entity=%s | entity_id=%s",
        user_id,
        action,
        entity,
        entity_id
    )

    return audit_log

def get_audit_logs(
        db: Session,
        skip: int = 0,
        limit: int = 10
):
    if skip < 0:
        raise ValueError("Skip cannot be negative")

    if limit <= 0:
        raise ValueError("Limit must be greater than 0")

    if limit > 100:
        raise ValueError("Limit cannot exceed 100")

    logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).offset(skip).limit(limit).all()

    logger.info(
        "Audit logs retrieved | count=%s | skip=%s | limit=%s",
        len(logs),
        skip,
        limit
    )

    return logs