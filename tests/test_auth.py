def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword",
            "full_name": "Test User"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert "password" not in data
    assert "password_hash" not in data

def test_login_user(client):
    client.post(
        "/auth/register",
        json={
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "testpassword",
            "full_name": "Login User"
        }
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "loginuser",
            "password": "testpassword"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"