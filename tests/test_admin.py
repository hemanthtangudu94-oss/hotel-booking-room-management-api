from app.models.user import User
from app.services.role_service import assign_role


def register_test_main_admin(client):
    """Create the test account before reserving its username as the main admin."""
    from app.core.config import settings

    configured_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "__temporary_test_reserved_name__"
    try:
        response = client.post(
            "/auth/register",
            json={
                "username": "mainadmin",
                "email": "mainadmin@example.com",
                "password": "testpassword",
                "full_name": "Main Admin",
            },
        )
    finally:
        settings.MAIN_ADMIN_USERNAME = configured_username
    return response


def test_admin_without_token(client):
    response = client.get("/admin/test")

    assert response.status_code == 401

def test_admin_without_role(client):
    # Register normal user
    client.post(
        "/auth/register",
        json={
            "username": "normaluser",
            "email": "normaluser@example.com",
            "password": "testpassword",
            "full_name": "Normal User"
        }
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "normaluser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    # Access admin endpoint
    response = client.get(
        "/admin/test",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

def test_admin_with_role(client, db):
    # Register admin user
    client.post(
        "/auth/register",
        json={
            "username": "testadmin",
            "email": "testadmin@example.com",
            "password": "testpassword",
            "full_name": "Test Admin"
        }
    )

    # Get the registered user from test database
    user = db.query(User).filter(
        User.username == "testadmin"
    ).first()

    # Assign ADMIN role
    assign_role(
        db,
        user.id,
        "ADMIN"
    )

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "testadmin",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    # Access admin endpoint
    response = client.get(
        "/admin/test",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Admin access granted"
    assert data["username"] == "testadmin"


def test_assign_role_invalid_user(db):
    import pytest

    with pytest.raises(ValueError, match="User not found"):
        assign_role(
            db=db,
            user_id=999999,
            role_name="ADMIN"
        )


def test_assign_duplicate_role(client, db):
    import pytest

    # Register a user
    response = client.post(
        "/auth/register",
        json={
            "username": "duplicateroleuser",
            "email": "duplicaterole@example.com",
            "password": "testpassword",
            "full_name": "Duplicate Role User"
        }
    )
    assert response.status_code == 201

    user = db.query(User).filter(
        User.username == "duplicateroleuser"
    ).first()

    assert user is not None

    # First assignment should succeed
    assign_role(db, user.id, "ADMIN")

    # Second assignment should be rejected
    with pytest.raises(
        ValueError,
        match="User already has this role"
    ):
        assign_role(db, user.id, "ADMIN")


def test_admin_list_users_without_token(client):
    response = client.get("/admin/users")

    assert response.status_code == 401


def test_admin_list_users_without_role(client):
    # Register a normal user
    register_response = client.post(
        "/auth/register",
        json={
            "username": "listnormaluser",
            "email": "listnormal@example.com",
            "password": "testpassword",
            "full_name": "List Normal User"
        }
    )
    assert register_response.status_code == 201

    # Login
    login_response = client.post(
        "/auth/login",
        data={
            "username": "listnormaluser",
            "password": "testpassword"
        }
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Attempt to list users without the ADMIN role
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_admin_list_users_with_role(client, db):
    # Register an admin user
    register_response = client.post(
        "/auth/register",
        json={
            "username": "listadmin",
            "email": "listadmin@example.com",
            "password": "testpassword",
            "full_name": "List Admin"
        }
    )
    assert register_response.status_code == 201

    admin_user = db.query(User).filter(
        User.username == "listadmin"
    ).first()
    assert admin_user is not None

    # Assign ADMIN role
    assign_role(db, admin_user.id, "ADMIN")

    # Login as admin
    login_response = client.post(
        "/auth/login",
        data={
            "username": "listadmin",
            "password": "testpassword"
        }
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Retrieve all users
    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    users = response.json()
    assert isinstance(users, list)
    assert any(user["username"] == "listadmin" for user in users)

    # Ensure sensitive password fields are not exposed
    for user in users:
        assert "password" not in user
        assert "password_hash" not in user


def test_main_admin_delete_user(client, db):
    # Register the main admin
    register_test_main_admin(client)

    admin = db.query(User).filter(
        User.username == "mainadmin"
    ).first()
    assert admin is not None

    # Register a target user
    client.post(
        "/auth/register",
        json={
            "username": "deleteuser",
            "email": "deleteuser@example.com",
            "password": "testpassword",
            "full_name": "Delete User"
        }
    )

    target = db.query(User).filter(
        User.username == "deleteuser"
    ).first()
    assert target is not None

    # Assign the designated main admin username for this test.
    from app.core.config import settings
    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        login = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.delete(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204
        assert db.get(User, target.id) is None

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username



def test_delete_user_not_found(client):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        # Register the main admin
        register_test_main_admin(client)

        # Login as the main admin
        login_response = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        # Attempt to delete a nonexistent user
        response = client.delete(
            "/admin/users/999999",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_other_admin_cannot_delete_user(client, db):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        # Register the designated main admin account
        register_test_main_admin(client)

        # Register another administrator
        client.post(
            "/auth/register",
            json={
                "username": "otheradmin",
                "email": "otheradmin@example.com",
                "password": "testpassword",
                "full_name": "Other Admin"
            }
        )

        other_admin = db.query(User).filter(
            User.username == "otheradmin"
        ).first()
        assert other_admin is not None

        assign_role(db, other_admin.id, "ADMIN")

        # Register a target user
        client.post(
            "/auth/register",
            json={
                "username": "targetuser",
                "email": "targetuser@example.com",
                "password": "testpassword",
                "full_name": "Target User"
            }
        )

        target = db.query(User).filter(
            User.username == "targetuser"
        ).first()
        assert target is not None

        # Login as the other administrator
        login_response = client.post(
            "/auth/login",
            data={
                "username": "otheradmin",
                "password": "testpassword"
            }
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        response = client.delete(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

        # Confirm the target user still exists
        assert db.get(User, target.id) is not None

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_main_admin_cannot_delete_user_with_booking(client, db):
    from datetime import date, timedelta
    from decimal import Decimal
    from app.core.config import settings
    from app.models.booking import Booking
    from app.models.room import Room
    from app.models.room_type import RoomType

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        # Register the main admin
        register_test_main_admin(client)

        # Register the user who will have a booking
        client.post(
            "/auth/register",
            json={
                "username": "bookinguser",
                "email": "bookinguser@example.com",
                "password": "testpassword",
                "full_name": "Booking User"
            }
        )

        admin_login = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert admin_login.status_code == 200
        token = admin_login.json()["access_token"]

        target = db.query(User).filter(
            User.username == "bookinguser"
        ).first()
        assert target is not None

        # Create a room type and room for the booking
        room_type = RoomType(
            name="Test Room Type",
            description="Test room",
            capacity=2,
            price_per_night=Decimal("100.00")
        )
        db.add(room_type)
        db.flush()

        room = Room(
            room_number="TEST-DEL-1",
            room_type_id=room_type.id,
            floor=1,
            status="AVAILABLE"
        )
        db.add(room)
        db.flush()

        today = date.today()
        booking = Booking(
            user_id=target.id,
            room_id=room.id,
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=2),
            status="CONFIRMED",
            total_amount=Decimal("100.00")
        )
        db.add(booking)
        db.commit()

        response = client.delete(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 409
        assert "booking history" in response.json()["detail"].lower()
        assert db.get(User, target.id) is not None

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_main_admin_update_user(client, db):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        # Register main admin
        register_test_main_admin(client)

        # Register target user
        client.post(
            "/auth/register",
            json={
                "username": "updateuser",
                "email": "updateuser@example.com",
                "password": "testpassword",
                "full_name": "Original Name"
            }
        )

        target = db.query(User).filter(
            User.username == "updateuser"
        ).first()
        assert target is not None

        # Login as main admin
        login = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.put(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "updateduser",
                "email": "updateduser@example.com",
                "full_name": "Updated Name"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updateduser@example.com"
        assert data["full_name"] == "Updated Name"
        assert "password_hash" not in data

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_update_user_not_found(client):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        register_test_main_admin(client)

        login = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.put(
            "/admin/users/999999",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "updateduser",
                "email": "updateduser@example.com",
                "full_name": "Updated Name"
            }
        )

        assert response.status_code == 404

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_update_user_duplicate_username(client, db):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        register_test_main_admin(client)

        client.post(
            "/auth/register",
            json={
                "username": "existinguser",
                "email": "existing@example.com",
                "password": "testpassword",
                "full_name": "Existing User"
            }
        )

        client.post(
            "/auth/register",
            json={
                "username": "targetuser",
                "email": "target@example.com",
                "password": "testpassword",
                "full_name": "Target User"
            }
        )

        target = db.query(User).filter(
            User.username == "targetuser"
        ).first()
        assert target is not None

        login = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.put(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "existinguser",
                "email": "newtarget@example.com",
                "full_name": "Target User"
            }
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Username already exists"

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_update_user_duplicate_email(client, db):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"

    try:
        register_test_main_admin(client)

        client.post(
            "/auth/register",
            json={
                "username": "existinguser",
                "email": "existing@example.com",
                "password": "testpassword",
                "full_name": "Existing User"
            }
        )

        client.post(
            "/auth/register",
            json={
                "username": "targetuser",
                "email": "target@example.com",
                "password": "testpassword",
                "full_name": "Target User"
            }
        )

        target = db.query(User).filter(
            User.username == "targetuser"
        ).first()
        assert target is not None

        login = client.post(
            "/auth/login",
            data={
                "username": "mainadmin",
                "password": "testpassword"
            }
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = client.put(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newtarget",
                "email": "existing@example.com",
                "full_name": "Target User"
            }
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Email already exists"

    finally:
        settings.MAIN_ADMIN_USERNAME = original_username


def test_main_admin_patch_user(client, db):
    from app.core.config import settings

    original_username = settings.MAIN_ADMIN_USERNAME
    settings.MAIN_ADMIN_USERNAME = "mainadmin"
    try:
        response = register_test_main_admin(client)
        assert response.status_code == 201
        response = client.post(
            "/auth/register",
            json={
                "username": "patchtarget", "email": "patchtarget@example.com",
                "password": "testpassword", "full_name": "patchtarget",
            },
        )
        assert response.status_code == 201

        login = client.post(
            "/auth/login", data={"username": "mainadmin", "password": "testpassword"}
        )
        target = db.query(User).filter(User.username == "patchtarget").first()
        response = client.patch(
            f"/admin/users/{target.id}",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            json={"full_name": "Patched Name"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Patched Name"
        assert response.json()["username"] == "patchtarget"
    finally:
        settings.MAIN_ADMIN_USERNAME = original_username
