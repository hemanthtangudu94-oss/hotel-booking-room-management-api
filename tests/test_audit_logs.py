from app.models.user import User
from app.services.role_service import assign_role
from app.services.audit_service import create_audit_log


def get_admin_headers(client, db):
    client.post(
        "/auth/register",
        json={
            "username": "auditadmin",
            "email": "auditadmin@example.com",
            "password": "testpassword",
            "full_name": "Audit Admin"
        }
    )

    user = db.query(User).filter(
        User.username == "auditadmin"
    ).first()

    assign_role(db, user.id, "ADMIN")

    login_response = client.post(
        "/auth/login",
        data={
            "username": "auditadmin",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_get_audit_logs(client, db):
    headers = get_admin_headers(client, db)

    response = client.get(
        "/audit-logs/",
        headers=headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_audit_logs_pagination(client, db):
    headers = get_admin_headers(client, db)

    response = client.get(
        "/audit-logs/?skip=0&limit=1",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 1

def test_get_audit_logs_without_admin_role(client, db):
    client.post(
        "/auth/register",
        json={
            "username": "normalaudituser",
            "email": "normalaudituser@example.com",
            "password": "testpassword",
            "full_name": "Normal Audit User"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "normalaudituser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/audit-logs/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403

def test_get_audit_logs_without_token(client):
    response = client.get("/audit-logs/")

    assert response.status_code == 401