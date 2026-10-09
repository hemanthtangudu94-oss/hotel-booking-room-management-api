# Hotel Booking & Room Management API

A REST API built with FastAPI and SQLite for managing hotel rooms, bookings, payments, users, and audit logs.

## Features

- User registration and login with JWT authentication
- Password hashing with Passlib and bcrypt
- Role-based access control for administrative endpoints
- Room type and room management
- Booking creation, listing, and cancellation
- Prevention of overlapping confirmed bookings for the same room
- Payment creation and payment history
- Audit logging for booking and payment actions
- SQLite database with SQLAlchemy
- Database schema migrations using Alembic
- Interactive API documentation with Swagger UI
- Automated tests using pytest

## Technology Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Alembic
- Pydantic
- JWT and OAuth2
- Passlib and bcrypt
- pytest

## Project Structure

```text
Hotel_Booking_API/
├── app/
│   ├── api/routes/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
│   └── versions/
├── tests/
├── README.md
├── .gitignore
├── alembic.ini
└── requirements.txt
```

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root with the following settings:

```dotenv
SECRET_KEY=replace_with_a_strong_random_secret_at_least_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate your own strong, random secret key. Keep it private and never commit `.env` to version control. The application requires `SECRET_KEY`; the other settings have defaults in `app/core/config.py`.


### 4. Apply database migrations

```powershell
alembic upgrade head
```

### 5. Start the API

```powershell
uvicorn app.main:app --reload
```

### 6. Open the API documentation

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc


## Running Tests

Run the automated test suite:

```powershell
pytest -v
```

**Verified test status:** 37 tests passed in the development environment.


## Authentication

1. Register through `POST /auth/register`.
2. Log in through `POST /auth/login` using the OAuth2 form fields `username` and `password`.
3. Copy the returned access token.
4. In Swagger UI, click **Authorize** and authenticate using the OAuth2 password flow.
5. Call protected endpoints according to the user's assigned role.

## Important Notes

- The default database configuration uses SQLite.
- Administrative endpoints require the `ADMIN` role.
- Users can access their own bookings and payments.
- Booking and payment operations include business-rule validation.
- Payment creation and payment audit logging are committed in a single database transaction.
- Never commit secrets, virtual environments, or local database files to a public repository.