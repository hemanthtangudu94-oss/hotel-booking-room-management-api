from unittest.mock import patch


def test_create_payment(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "paymentuser",
            "email": "paymentuser@example.com",
            "password": "testpassword",
            "full_name": "Payment User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "paymentuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-05-01",
            "check_out": "2027-05-03"
        }
    )

    assert booking_response.status_code == 201

    booking = booking_response.json()

    # Create payment
    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "amount": 7000,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["booking_id"] == booking["id"]
    assert data["amount"] == 7000
    assert data["status"] == "PAID"
    assert data["payment_method"] == "CARD"
    assert data["paid_at"] is not None

def test_duplicate_payment(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "duplicatepayment",
            "email": "duplicatepayment@example.com",
            "password": "testpassword",
            "full_name": "Duplicate Payment User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "duplicatepayment",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-06-01",
            "check_out": "2027-06-03"
        }
    )

    assert booking_response.status_code == 201

    booking = booking_response.json()

    # First payment
    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "amount": 7000,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 201

    # Second payment for same booking
    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "amount": 7000,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Booking has already been paid"

def test_invalid_payment_amount(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "invalidpayment",
            "email": "invalidpayment@example.com",
            "password": "testpassword",
            "full_name": "Invalid Payment User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "invalidpayment",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-07-01",
            "check_out": "2027-07-03"
        }
    )

    assert booking_response.status_code == 201

    booking = booking_response.json()

    # Try incorrect payment amount
    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "amount": 5000,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Payment amount does not match booking amount"

def test_payment_for_cancelled_booking(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "cancelpayment",
            "email": "cancelpayment@example.com",
            "password": "testpassword",
            "full_name": "Cancel Payment User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "cancelpayment",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-08-01",
            "check_out": "2027-08-03"
        }
    )

    assert booking_response.status_code == 201

    booking = booking_response.json()

    # Cancel booking
    cancel_response = client.patch(
        f"/bookings/{booking['id']}/cancel",
        headers=headers
    )

    assert cancel_response.status_code == 200

    # Try to pay for cancelled booking
    response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "amount": 7000,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Payment cannot be made for this booking"

def test_get_payments(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "getpaymentuser",
            "email": "getpaymentuser@example.com",
            "password": "testpassword",
            "full_name": "Get Payment User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "getpaymentuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-09-01",
            "check_out": "2027-09-03"
        }
    )

    assert booking_response.status_code == 201

    booking = booking_response.json()

    # Create payment
    payment_response = client.post(
        "/payments/",
        headers=headers,
        json={
            "booking_id": booking["id"],
            "amount": 7000,
            "payment_method": "CARD"
        }
    )

    assert payment_response.status_code == 201

    # Get payments
    response = client.get(
        "/payments/",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["booking_id"] == booking["id"]
    assert data[0]["amount"] == 7000
    assert data[0]["status"] == "PAID"

def test_database_prevents_duplicate_paid_payments(client, db):
    from sqlalchemy.exc import IntegrityError
    from app.models.payments import Payment
    from app.models.booking import Booking

    # Register and log in a user
    client.post(
        "/auth/register",
        json={
            "username": "dbpaymentuser",
            "email": "dbpaymentuser@example.com",
            "password": "testpassword",
            "full_name": "DB Payment User"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "dbpaymentuser",
            "password": "testpassword"
        }
    )

    headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # Create a booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-10-01",
            "check_out": "2027-10-03"
        }
    )

    assert booking_response.status_code == 201
    booking_id = booking_response.json()["id"]

    # Insert the first paid payment directly
    db.add(Payment(
        booking_id=booking_id,
        amount=7000,
        status="PAID",
        payment_method="CARD"
    ))
    db.commit()

    # Attempt a second paid payment for the same booking
    db.add(Payment(
        booking_id=booking_id,
        amount=7000,
        status="PAID",
        payment_method="UPI"
    ))

    try:
        db.commit()
        assert False, "Database allowed duplicate PAID payments"
    except IntegrityError:
        db.rollback()


def test_payment_rolled_back_when_audit_logging_fails(client, db):
    from app.models.payments import Payment
    from app.models.booking import Booking

    # Register a user
    client.post(
        "/auth/register",
        json={
            "username": "auditfailuser",
            "email": "auditfailuser@example.com",
            "password": "testpassword",
            "full_name": "Audit Failure User"
        }
    )

    # Log in
    login_response = client.post(
        "/auth/login",
        data={
            "username": "auditfailuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-11-01",
            "check_out": "2027-11-03"
        }
    )

    assert booking_response.status_code == 201
    booking_id = booking_response.json()["id"]

    # Simulate audit logging failure
    with patch(
        "app.services.payment_service.create_audit_log",
        side_effect=ValueError("Simulated audit failure")
    ):
        response = client.post(
            "/payments/",
            headers=headers,
            json={
                "booking_id": booking_id,
                "amount": 7000,
                "payment_method": "CARD"
            }
        )

    assert response.status_code == 400

    # Confirm no payment was persisted
    payment = db.query(Payment).filter(
        Payment.booking_id == booking_id
    ).first()

    assert payment is None
