from app.models.user import User
from app.services.role_service import assign_role


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