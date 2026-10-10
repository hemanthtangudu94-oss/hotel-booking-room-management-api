import logging


from datetime import datetime, timezone

from sqlalchemy.orm import Session


from app.models.booking import Booking
from app.models.payments import Payment
from app.schemas.payment import PaymentCreate
from app.services.audit_service import create_audit_log



logger = logging.getLogger(__name__)


def create_payment(
        db: Session,
        payment_data: PaymentCreate,
        user_id: int
):

    #checking whether booking exists
    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id,
        Booking.user_id == user_id
    ).first()

    if booking is None:
        raise ValueError("Booking not found")

    #checking booking status
    if booking.status != "CONFIRMED":
        raise ValueError("Payment cannot be made for this booking")

    #Validating payment amount
    if payment_data.amount != booking.total_amount:
        raise ValueError("Payment amount does not match booking amount")

    #checking whether payment already exists
    existing_payment = db.query(Payment).filter(
        Payment.booking_id == payment_data.booking_id,
        Payment.status == "PAID"
    ).first()

    if existing_payment:
        raise ValueError("Booking has already been paid")

    #creating payment
    payment = Payment(
        booking_id=payment_data.booking_id,
        amount=payment_data.amount,
        status="PAID",
        payment_method=payment_data.payment_method,
        paid_at=datetime.now(timezone.utc)
    )

    db.add(payment)

    try:
        db.flush()

        create_audit_log(
            db=db,
            user_id=user_id,
            action="CREATE",
            entity="Payment",
            entity_id=payment.id,
            new_value=(
                f"Booking ID: {payment.booking_id},"
                f"Amount: {payment.amount},"
                f"Status: {payment.status}"
            ),
            commit=False
        )
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise


    logger.info(
        "Payment created | user_id=%s | payment_id=%s | booking_id=%s | amount=%s",
        user_id,
        payment.id,
        payment.booking_id,
        payment.amount
    )

    return payment

def get_payments(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10
):
    if skip < 0 :
        raise ValueError("Skip cannot be negative")

    if limit <= 0:
        raise ValueError("Limit must be greater than 0")

    if limit > 100:
        raise ValueError("Limit cannot exceed 100")
    
    payments = db.query(Payment).join(
        Booking,
        Payment.booking_id == Booking.id
    ).filter(
        Booking.user_id == user_id
    ).order_by(
        Payment.id.desc()
    ).offset(skip).limit(limit).all()

    logger.info(
        "Payments retrieved | user_id=%s | count=%s",
        user_id,
        len(payments)
    )
    return payments