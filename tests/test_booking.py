from decimal import Decimal

from unittest.mock import patch

from app.services import booking_service

def test_create_booking(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "bookinguser",
            "email": "bookinguser@example.com",
            "password": "testpassword",
            "full_name": "Booking User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "bookinguser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    # Create booking
    response = client.post(
        "/bookings/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "room_id": 1,
            "check_in": "2026-12-01",
            "check_out": "2026-12-03"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["room_id"] == 1
    assert data["check_in"] == "2026-12-01"
    assert data["check_out"] == "2026-12-03"
    assert data["status"] == "CONFIRMED"
    assert Decimal(data["total_amount"]) == Decimal("7000.00")

def test_overlapping_booking(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "overlapuser",
            "email": "overlapuser@example.com",
            "password": "testpassword",
            "full_name": "Overlap User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "overlapuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create first booking
    response = client.post(
        "/bookings/",
        json={
            "room_id": 1,
            "check_in": "2027-01-10",
            "check_out": "2027-01-15"
        },
        headers=headers
    )

    assert response.status_code == 201

    # Try overlapping booking
    response = client.post(
        "/bookings/",
        json={
            "room_id": 1,
            "check_in": "2027-01-12",
            "check_out": "2027-01-14"
        },
        headers=headers
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Room is already booked for the selected dates"

def test_invalid_booking_dates(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "dateuser",
            "email": "dateuser@example.com",
            "password": "testpassword",
            "full_name": "Date User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "dateuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    # Try booking with invalid dates
    response = client.post(
        "/bookings/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "room_id": 1,
            "check_in": "2027-02-15",
            "check_out": "2027-02-10"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Check-out date must be after check-in date"

def test_booking_invalid_room(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "roomuser",
            "email": "roomuser@example.com",
            "password": "testpassword",
            "full_name": "Room User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "roomuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    # Try booking a non-existent room
    response = client.post(
        "/bookings/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "room_id": 999,
            "check_in": "2027-03-10",
            "check_out": "2027-03-12"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Room not found"

def test_get_bookings(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "getbookinguser",
            "email": "getbookinguser@example.com",
            "password": "testpassword",
            "full_name": "Get Booking User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "getbookinguser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create booking
    client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-04-10",
            "check_out": "2027-04-12"
        }
    )

    # Get bookings
    response = client.get(
        "/bookings/",
        headers=headers,
        params={
            "skip": 0,
            "limit": 10
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["room_id"] == 1
    assert data[0]["check_in"] == "2027-04-10"
    assert data[0]["check_out"] == "2027-04-12"

def test_cancel_booking(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "canceluser",
            "email": "canceluser@example.com",
            "password": "testpassword",
            "full_name": "Cancel User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "canceluser",
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
            "check_in": "2027-05-10",
            "check_out": "2027-05-12"
        }
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    # Cancel booking
    response = client.patch(
        f"/bookings/{booking_id}/cancel",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["status"] == "CANCELLED"

def test_cancel_already_cancelled_booking(client):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "doublecanceluser",
            "email": "doublecanceluser@example.com",
            "password": "testpassword",
            "full_name": "Double Cancel User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "doublecanceluser",
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
            "check_in": "2027-06-10",
            "check_out": "2027-06-12"
        }
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    # Cancel booking first time
    response = client.patch(
        f"/bookings/{booking_id}/cancel",
        headers=headers
    )

    assert response.status_code == 200

    # Try cancelling again
    response = client.patch(
        f"/bookings/{booking_id}/cancel",
        headers=headers
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Booking cannot be cancelled"


def test_create_booking_rolls_back_if_audit_fails(client, db):
    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "auditfailuser",
            "email": "auditfailuser@example.com",
            "password": "testpassword",
            "full_name": "Audit Fail User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "auditfailuser",
            "password": "testpassword"
        }
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Make audit-log creation fail
    with patch.object(
        booking_service,
        "create_audit_log",
        side_effect=RuntimeError("Simulated audit failure")
    ):
        response = client.post(
            "/bookings/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "room_id": 1,
                "check_in": "2027-08-10",
                "check_out": "2027-08-12"
            }
        )

    assert response.status_code == 500

    # Confirm the booking was not saved
    from app.models.booking import Booking

    booking = db.query(Booking).filter(
        Booking.check_in == "2027-08-10",
        Booking.check_out == "2027-08-12"
    ).first()

    assert booking is None


def test_cancel_booking_rolls_back_if_audit_fails(client, db):
    from unittest.mock import patch
    from app.models.booking import Booking
    from app.services import booking_service

    # Register user
    client.post(
        "/auth/register",
        json={
            "username": "cancelaudituser",
            "email": "cancelaudituser@example.com",
            "password": "testpassword",
            "full_name": "Cancel Audit User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "cancelaudituser",
            "password": "testpassword"
        }
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a booking
    booking_response = client.post(
        "/bookings/",
        headers=headers,
        json={
            "room_id": 1,
            "check_in": "2027-09-10",
            "check_out": "2027-09-12"
        }
    )
    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    # Fail audit logging during cancellation
    with patch.object(
        booking_service,
        "create_audit_log",
        side_effect=RuntimeError("Simulated audit failure")
    ):
        response = client.patch(
            f"/bookings/{booking_id}/cancel",
            headers=headers
        )

    assert response.status_code == 500

    # Verify cancellation was rolled back
    db.expire_all()
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    assert booking is not None
    assert booking.status == "CONFIRMED"
