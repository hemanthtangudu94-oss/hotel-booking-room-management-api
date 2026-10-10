from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import create_payment, get_payments


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_payment_endpoint(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return create_payment(
            db,
            payment_data,
            current_user.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

@router.get(
    "/",
    response_model=list[PaymentResponse]
)
def get_payments_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_payments(
        db,
        current_user.id,
        skip,
        limit
    )