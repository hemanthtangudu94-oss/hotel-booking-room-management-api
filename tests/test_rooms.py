from app.models.user import User
from app.services.role_service import assign_role


def get_admin_headers(
    client,
    db,
    username="testadmin",
    email="testadmin@example.com"
):
    # Register admin user
    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "testpassword",
            "full_name": "Test Admin"
        }
    )

    # Get user from test database
    user = db.query(User).filter(
        User.username == username
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
            "username": username,
            "password": "testpassword"
        }
    )

    # Get access token
    token = login_response.json()["access_token"]

    # Return authorization headers
    return {
        "Authorization": f"Bearer {token}"
    }

def test_create_room_type(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/room-types/",
        headers=headers,
        json={
            "name": "Suite",
            "description": "Test Deluxe Room",
            "capacity": 2,
            "price_per_night": 3500
        }
    )

    assert response.status_code == 201

def test_room_type_invalid_capacity(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/room-types/",
        headers=headers,
        json={
            "name": "Invalid Capacity",
            "description": "Invalid room type",
            "capacity": 0,
            "price_per_night": 3500
        }
    )

    assert response.status_code == 422




def test_room_type_invalid_price(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/room-types/",
        headers=headers,
        json={
            "name": "Invalid Price",
            "description": "Invalid room type",
            "capacity": 2,
            "price_per_night": 0
        }
    )

    assert response.status_code == 422




def test_duplicate_room_type(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/room-types/",
        headers=headers,
        json={
            "name": "Deluxe",
            "description": "Duplicate room type",
            "capacity": 2,
            "price_per_night": 3500
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Room type already exists"

def test_create_room(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "102",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["room_number"] == "102"
    assert data["room_type_id"] == 1
    assert data["floor"] == 1
    assert data["status"] == "AVAILABLE"

def test_create_room_invalid_room_type(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "103",
            "room_type_id": 999,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Room type not found"


def test_create_room_invalid_floor(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "104",
            "room_type_id": 1,
            "floor": 0,
            "status": "AVAILABLE"
        }
    )

    assert response.status_code == 422


def test_create_room_invalid_status(client, db):
    headers = get_admin_headers(client, db)

    response = client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "113",
            "room_type_id": 1,
            "floor": 1,
            "status": "BROKEN_STATUS"
        }
    )

    assert response.status_code == 422



def test_get_rooms(client, db):
    headers = get_admin_headers(client, db)

    # Create room
    response = client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "105",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    assert response.status_code == 201

    # Get rooms
    response = client.get(
        "/rooms/",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert any(room["room_number"] == "105" for room in data)

def test_get_rooms_pagination(client, db):
    headers = get_admin_headers(client, db)

    # Create two rooms
    client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "106",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "107",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    # Get first page
    response = client.get(
        "/rooms/?skip=0&limit=1",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

def test_get_rooms_filtering(client, db):
    headers = get_admin_headers(client, db)

    # Create an unavailable room
    response = client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "108",
            "room_type_id": 1,
            "floor": 1,
            "status": "MAINTENANCE"
        }
    )

    assert response.status_code == 201

    # Filter by status
    response = client.get(
        "/rooms/?room_status=MAINTENANCE",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for room in data:
        assert room["status"] == "MAINTENANCE"

def test_get_rooms_sorting_ascending(client, db):
    headers = get_admin_headers(client, db)

    # Create rooms
    client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "110",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "109",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    # Get rooms sorted ascending
    response = client.get(
        "/rooms/?sort_by=room_number&sort_order=asc",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    room_numbers = [room["room_number"] for room in data]

    assert room_numbers == sorted(room_numbers)

def test_get_rooms_sorting_descending(client, db):
    headers = get_admin_headers(client, db)

    client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "111",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    client.post(
        "/rooms/",
        headers=headers,
        json={
            "room_number": "112",
            "room_type_id": 1,
            "floor": 1,
            "status": "AVAILABLE"
        }
    )

    response = client.get(
        "/rooms/?sort_by=room_number&sort_order=desc",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    room_numbers = [room["room_number"] for room in data]

    assert room_numbers == sorted(room_numbers, reverse=True)

def test_get_rooms_invalid_sort_field(client, db):
    headers = get_admin_headers(client, db)

    response = client.get(
        "/rooms/?sort_by=invalid_field&sort_order=asc",
        headers=headers
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Invalid sort field")


def test_get_rooms_invalid_sort_order(client, db):
    headers = get_admin_headers(client, db)

    response = client.get(
        "/rooms/?sort_by=room_number&sort_order=random",
        headers=headers
    )

    assert response.status_code == 400
    assert "Invalid sort order" in response.json()["detail"]


def test_room_type_crud_and_delete_guard(client, db):
    headers = get_admin_headers(client, db)
    listed = client.get("/room-types/", headers=headers)
    assert listed.status_code == 200
    assert any(item["name"] == "Deluxe" for item in listed.json())

    room_type_id = listed.json()[0]["id"]
    fetched = client.get(f"/room-types/{room_type_id}", headers=headers)
    assert fetched.status_code == 200

    updated = client.patch(
        f"/room-types/{room_type_id}", headers=headers,
        json={"description": "Updated description"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated description"

    replaced = client.put(
        f"/room-types/{room_type_id}", headers=headers,
        json={
            "name": "Deluxe Updated", "description": "Full update",
            "capacity": 3, "price_per_night": "4000.00",
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["capacity"] == 3

    blocked = client.delete(f"/room-types/{room_type_id}", headers=headers)
    assert blocked.status_code == 409


def test_room_crud_and_delete_guard(client, db):
    headers = get_admin_headers(client, db)
    created = client.post(
        "/rooms/", headers=headers,
        json={"room_number": "201", "room_type_id": 1, "floor": 2},
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    fetched = client.get(f"/rooms/{room_id}", headers=headers)
    assert fetched.status_code == 200

    replaced = client.put(
        f"/rooms/{room_id}", headers=headers,
        json={
            "room_number": "202", "room_type_id": 1,
            "floor": 3, "status": "MAINTENANCE",
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["room_number"] == "202"

    patched = client.patch(
        f"/rooms/{room_id}", headers=headers, json={"status": "CLEANING"}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "CLEANING"

    deleted = client.delete(f"/rooms/{room_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/rooms/{room_id}", headers=headers).status_code == 404


def test_patch_rejects_empty_and_null_room_updates(client, db):
    headers = get_admin_headers(client, db)
    assert client.patch("/rooms/1", headers=headers, json={}).status_code == 422
    assert client.patch(
        "/rooms/1", headers=headers, json={"status": None}
    ).status_code == 422
