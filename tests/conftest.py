import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.models.room_type import RoomType
from app.models.room import Room
from app.db.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = "sqlite:///./test_hotel_booking.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Create test room type
    room_type = RoomType(
        name="Deluxe",
        description="Test Deluxe Room",
        capacity=2,
        price_per_night=3500
    )

    db.add(room_type)
    db.commit()
    db.refresh(room_type)

    # Create test room
    room = Room(
        room_number="101",
        room_type_id=room_type.id,
        floor=1,
        status="AVAILABLE"
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()