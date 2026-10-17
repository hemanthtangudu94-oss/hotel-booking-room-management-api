# Streamlit frontend

This frontend connects to the existing FastAPI service over HTTP. It uses the API's own authentication and authorization rules; it does not store passwords or API secrets in source code.

## Start the API

In a terminal at the project root, activate the existing Python environment if you use one, then run:

```powershell
uvicorn app.main:app --reload
```

The default API address is `http://127.0.0.1:8000`.

## Install and run the frontend

Open a second terminal at the project root:

```powershell
python -m pip install -r frontend-requirements.txt
streamlit run streamlit_app.py
```

If the API uses another address, set `HOTEL_API_URL` before starting Streamlit, or change the FastAPI base URL in the frontend sidebar/login screen. For example:

```powershell
$env:HOTEL_API_URL = "http://127.0.0.1:8000"
streamlit run streamlit_app.py
```

## Sign in and permissions

Register or sign in from the frontend. The token is held in the Streamlit session and sent as a bearer token to the API. Sign out or close the session to clear it. Never put passwords, JWTs, or signing keys in source files.

- Registration creates a standard `USER` account. An administrator assigns employee access from **User management → Access role**; users cannot select their own role.
- Standard users see Available rooms and Bookings. They can manage only their own bookings and payments; room browsing uses `GET /rooms/available`.
- Employees can review all bookings and reschedule or cancel them, view the full room list, and update room operational status. They cannot create guest bookings, access payments, edit room details or pricing, manage users, or view audit logs.
- Administrators retain the full management screens. The configured main administrator controls user edits, deletion, password resets, and role assignments. Password reset stores only a hash and never reveals the previous password.
- Role checks are enforced by FastAPI as well as the Streamlit navigation.
- The API does not expose payment editing, deletion, or refunds. Booking cancellation retains history.
- There is no admin-only user creation endpoint; new accounts use `/auth/register`.

The frontend reports API validation, authorization, and connection errors inline. Its screens call only routes implemented by this project.
