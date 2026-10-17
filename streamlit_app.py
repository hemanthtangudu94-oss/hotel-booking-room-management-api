"""Streamlit frontend for the Hotel Booking & Room Management API."""

from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import httpx
import streamlit as st


st.set_page_config(page_title="Hotel Manager", page_icon="🏨", layout="wide")

DEFAULT_API_URL = os.getenv("HOTEL_API_URL", "http://127.0.0.1:8000").rstrip("/")


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def friendly_error(status_code: int, detail, *, path: str = "") -> str:
    """Turn FastAPI errors into short, actionable messages for the UI."""
    if status_code == 401:
        if path == "/auth/login":
            return "The username or password is incorrect. Please try again."
        return "Your sign-in has expired. Please sign in again."

    if status_code == 403:
        text = str(detail).casefold()
        if "main administrator" in text:
            return "Only the configured main administrator can change or reset user accounts."
        return "Your account does not have permission to do this. Contact an administrator if you need access."

    if status_code == 404:
        return "That record could not be found. It may have been removed."
    if status_code == 409:
        text = str(detail).casefold()
        if "room type is in use" in text or "room type" in text and "in use" in text:
            return "This room type is assigned to one or more rooms, so it cannot be deleted yet."
        if "booking history" in text:
            return "This record has booking history and cannot be deleted."
        return "This change conflicts with existing data. Refresh the list and try again."
    if status_code == 422:
        if isinstance(detail, list):
            issues = []
            for item in detail:
                if not isinstance(item, dict):
                    continue
                location = [str(part).replace("_", " ") for part in item.get("loc", []) if part not in {"body", "query", "path"}]
                message = str(item.get("msg", "Check this value.")).removeprefix("Value error, ")
                issues.append(f"{' '.join(location).capitalize()}: {message}" if location else message)
            if issues:
                return "Please check the information entered:\n\n" + "\n".join(f"• {issue}" for issue in issues)
        return "Some information is missing or invalid. Check the fields and try again."
    if status_code >= 500:
        return "The server could not complete the request. Please try again in a moment."

    text = str(detail).strip()
    known = {
        "room is already booked for the selected dates": "That room is already booked for those dates. Choose another room or dates.",
        "room is not available for booking": "That room is not currently available. Choose an available room.",
        "check-out date must be after check-in date": "Check-out must be later than check-in.",
        "a paid booking cannot be updated": "This booking cannot be changed because it has already been paid.",
        "booking has already been paid": "This booking has already been paid.",
        "payment amount does not match booking amount": "The payment amount must match the booking total.",
        "cannot delete a user who has booking history": "This user has booking history and cannot be deleted.",
    }
    if text.casefold() in known:
        return known[text.casefold()]
    if text:
        return text[:1].upper() + text[1:]
    return "The request could not be completed. Please review your information and try again."


def api_request(method: str, path: str, *, params=None, payload=None, form=None):
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = httpx.request(
            method,
            f"{st.session_state.api_url}{path}",
            params=params,
            json=payload,
            data=form,
            headers=headers,
            timeout=12.0,
        )
    except httpx.RequestError as exc:
        raise APIError(
            f"We couldn't connect to the hotel service at {st.session_state.api_url}. "
            "Check that the API is running and the address is correct."
        ) from exc

    if response.status_code >= 400:
        try:
            body = response.json()
            detail = body.get("detail", body)
        except ValueError:
            detail = response.text or response.reason_phrase
        if response.status_code == 401:
            st.session_state.pop("token", None)
            st.session_state.pop("username", None)
        raise APIError(friendly_error(response.status_code, detail, path=path), response.status_code)
    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def show_error(exc: Exception):
    st.error(str(exc))


def load(path: str, *, params=None):
    try:
        return api_request("GET", path, params=params)
    except APIError as exc:
        show_error(exc)
        return None


def changed(method: str, path: str, payload=None, *, params=None, success="Saved"):
    try:
        api_request(method, path, payload=payload, params=params)
        st.session_state.flash_message = success
        st.rerun()
    except APIError as exc:
        show_error(exc)


def table(items, *, empty="No records found."):
    if items:
        st.dataframe(items, use_container_width=True, hide_index=True)
    else:
        st.info(empty)


def search_items(items, query, *fields):
    """Filter a loaded API page locally while keeping the API response intact."""
    if not query:
        return items
    needle = query.strip().casefold()
    return [
        item for item in items
        if any(needle in str(item.get(field, "")).casefold() for field in fields)
    ]


def record_picker(items, label, key, display):
    if not items:
        return None
    options = {display(item): item for item in items}
    selected = st.selectbox(label, list(options), key=key)
    return options[selected]


def inr(amount):
    """Format API monetary values as Indian rupees."""
    return f"₹{Decimal(str(amount)):,.2f}"


def room_option_label(room):
    room_type = room.get("room_type_name") or f"Type {room.get('room_type_id', '')}"
    price = inr(room["price_per_night"]) if room.get("price_per_night") is not None else "price set by hotel"
    return f"Room {room['room_number']} · {room_type} · floor {room['floor']} · {price} per night"


def login_screen():
    st.title("🏨 Hotel Booking & Room Management")
    st.caption("Connect to your FastAPI service to manage rooms and bookings.")
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Sign in")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            try:
                token_data = api_request(
                    "POST", "/auth/login", form={"username": username, "password": password}
                )
                st.session_state.token = token_data["access_token"]
                st.session_state.username = username
                st.session_state.pop("is_admin", None)
                st.session_state.pop("is_employee", None)
                st.session_state.pop("role", None)
                st.rerun()
            except APIError as exc:
                show_error(exc)
    with right:
        st.subheader("Create an account")
        with st.form("register"):
            new_username = st.text_input("Username", key="register_username")
            email = st.text_input(
                "Email address",
                placeholder="name@example.com",
                help="Enter your complete email address.",
                key="register_email",
            )
            full_name = st.text_input("Full name")
            new_password = st.text_input("Password (at least 8 characters)", type="password", key="register_password")
            submitted = st.form_submit_button("Register", use_container_width=True)
        if submitted:
            email = email.strip()
            if not email:
                st.error("Enter your email address.")
            else:
                try:
                    api_request("POST", "/auth/register", payload={
                        "username": new_username,
                        "email": email,
                        "full_name": full_name,
                        "password": new_password,
                    })
                    st.success("Account created. Sign in to continue.")
                except APIError as exc:
                    show_error(exc)


def rooms_page():
    st.title("Rooms")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.5])
    with col1:
        status = st.selectbox("Filter by status", ["All", "AVAILABLE", "MAINTENANCE", "CLEANING"])
    with col2:
        sort_by = st.selectbox("Sort by", ["room_number", "floor", "status"])
    with col3:
        sort_order = st.selectbox("Order", ["asc", "desc"])
    with col4:
        query = st.text_input("Find a room", placeholder="Room number or floor")
    params = {"skip": 0, "limit": 100, "sort_by": sort_by, "sort_order": sort_order}
    if status != "All":
        params["room_status"] = status
    rooms = load("/rooms/", params=params)
    if rooms is not None:
        visible_rooms = search_items(rooms, query, "room_number", "floor", "status", "room_type_id")
        st.caption(f"Showing {len(visible_rooms)} of {len(rooms)} rooms on this page")
        table(visible_rooms)
        selected_room = record_picker(
            visible_rooms, "Quick room details", "room_quick_detail",
            lambda room: f"Room {room['room_number']} · {room['status']} · floor {room['floor']}"
        )
        if selected_room:
            st.info(f"Room **{selected_room['room_number']}** · type ID {selected_room['room_type_id']} · floor {selected_room['floor']} · **{selected_room['status']}**")
    room_types = load("/room-types/")
    type_options = {f"{item['name']} (ID {item['id']})": item["id"] for item in (room_types or [])}
    create_tab, edit_tab, remove_tab = st.tabs(["Add room", "Edit room", "Delete room"])
    with create_tab:
        if not type_options:
            st.info("Add a room type before creating a room.")
        else:
            with st.form("room_create"):
                number = st.text_input("Room number", max_chars=10)
                type_label = st.selectbox("Room type", list(type_options))
                floor = st.number_input("Floor", min_value=1, step=1)
                room_status = st.selectbox("Status", ["AVAILABLE", "MAINTENANCE", "CLEANING"])
                submit = st.form_submit_button("Create room")
            if submit:
                changed("POST", "/rooms/", {"room_number": number, "room_type_id": type_options[type_label], "floor": int(floor), "status": room_status}, success="Room created.")
    with edit_tab:
        if rooms:
            room_map = {f"{r['room_number']} · {r['status']} (ID {r['id']})": r for r in rooms}
            label = st.selectbox("Select room", list(room_map), key="room_edit_select")
            room = room_map[label]
            with st.form("room_edit"):
                number = st.text_input("Room number", value=room["room_number"], max_chars=10)
                type_labels = list(type_options)
                current_label = next((k for k, v in type_options.items() if v == room["room_type_id"]), type_labels[0] if type_labels else None)
                if current_label is None:
                    st.warning("No room types are available.")
                    submit = False
                else:
                    type_label = st.selectbox("Room type", type_labels, index=type_labels.index(current_label))
                    floor = st.number_input("Floor", min_value=1, value=max(1, room["floor"]), step=1)
                    room_status = st.selectbox("Status", ["AVAILABLE", "MAINTENANCE", "CLEANING"], index=["AVAILABLE", "MAINTENANCE", "CLEANING"].index(room["status"]))
                    submit = st.form_submit_button("Save changes")
            if submit and current_label:
                changed("PUT", f"/rooms/{room['id']}", {"room_number": number, "room_type_id": type_options[type_label], "floor": int(floor), "status": room_status}, success="Room updated.")
        else:
            st.info("Load rooms to edit one.")
    with remove_tab:
        if rooms:
            room_map = {f"{r['room_number']} (ID {r['id']})": r for r in rooms}
            label = st.selectbox("Room to delete", list(room_map), key="room_delete_select")
            if st.button("Delete selected room", type="primary"):
                changed("DELETE", f"/rooms/{room_map[label]['id']}", success="Room deleted.")


def available_rooms_page():
    st.title("Available rooms")
    st.write("Browse rooms that are currently marked available, then start a booking with your selection.")
    rooms = load("/rooms/available", params={"skip": 0, "limit": 100})
    if rooms is None:
        return
    if not rooms:
        st.info("There are no available rooms right now. Please check again later or contact the hotel.")
        return

    query = st.text_input("Find a room", placeholder="Room number or room type")
    visible_rooms = search_items(rooms, query, "room_number", "room_type_name", "floor", "capacity")
    st.caption(f"Showing {len(visible_rooms)} of {len(rooms)} available rooms")
    if not visible_rooms:
        st.info("No available rooms match that search.")
        return

    columns = st.columns(2)
    for index, room in enumerate(visible_rooms):
        with columns[index % 2]:
            with st.container(border=True):
                st.subheader(f"Room {room['room_number']}")
                st.markdown(f"**{room['room_type_name']}** · floor {room['floor']}")
                st.caption(f"Capacity: {room['capacity']} · Status: Available")
                st.markdown(f"### {inr(room['price_per_night'])} **/ night**")
                if st.button("Book this room", key=f"book_available_room_{room['id']}", use_container_width=True):
                    st.session_state.booking_room_id = room["id"]
                    go_to_page("Bookings")


def room_types_page():
    st.title("Room types")
    items = load("/room-types/")
    if items is not None:
        query = st.text_input("Search room types", placeholder="Name or description")
        visible_items = search_items(items, query, "name", "description", "capacity", "price_per_night")
        st.caption(f"Showing {len(visible_items)} of {len(items)} room types")
        table(visible_items)
        selected_type = record_picker(
            visible_items, "Room type details", "type_quick_detail",
            lambda item: f"{item['name']} · capacity {item['capacity']}"
        )
        if selected_type:
            st.info(f"**{selected_type['name']}** · capacity {selected_type['capacity']} · {inr(selected_type['price_per_night'])} per night\n\n{selected_type['description'] or 'No description provided.'}")
    create_tab, edit_tab, delete_tab = st.tabs(["Add room type", "Edit room type", "Delete room type"])
    with create_tab:
        with st.form("type_create"):
            name = st.text_input("Name", max_chars=50)
            description = st.text_area("Description", max_chars=500)
            capacity = st.number_input("Capacity", min_value=1, step=1)
            price = st.number_input("Price per night", min_value=0.01, step=10.0, format="%.2f")
            submit = st.form_submit_button("Create room type")
        if submit:
            changed("POST", "/room-types/", {"name": name, "description": description or None, "capacity": int(capacity), "price_per_night": str(price)}, success="Room type created.")
    if items:
        item_map = {f"{i['name']} (ID {i['id']})": i for i in items}
        with edit_tab:
            label = st.selectbox("Select room type", list(item_map), key="type_edit_select")
            item = item_map[label]
            with st.form("type_edit"):
                name = st.text_input("Name", value=item["name"], max_chars=50)
                description = st.text_area("Description", value=item["description"] or "", max_chars=500)
                capacity = st.number_input("Capacity", min_value=1, value=item["capacity"], step=1)
                price = st.number_input("Price per night", min_value=0.01, value=float(item["price_per_night"]), step=10.0, format="%.2f")
                submit = st.form_submit_button("Save changes")
            if submit:
                changed("PUT", f"/room-types/{item['id']}", {"name": name, "description": description or None, "capacity": int(capacity), "price_per_night": str(price)}, success="Room type updated.")
        with delete_tab:
            label = st.selectbox("Room type to delete", list(item_map), key="type_delete_select")
            if st.button("Delete selected room type", type="primary"):
                changed("DELETE", f"/room-types/{item_map[label]['id']}", success="Room type deleted.")
    else:
        st.info("Create a room type to enable editing and deletion.")


def bookings_page():
    if st.session_state.get("is_employee"):
        employee_bookings_page()
        return
    st.title("My bookings")
    items = load("/bookings/", params={"skip": 0, "limit": 100})
    payments = load("/payments/", params={"skip": 0, "limit": 100})
    paid_booking_ids = {
        payment["booking_id"] for payment in (payments or []) if payment["status"] == "PAID"
    }
    if items is not None:
        filter_col, search_col = st.columns([1, 2])
        with filter_col:
            booking_status = st.selectbox("Booking status", ["All", "CONFIRMED", "CANCELLED"])
        with search_col:
            query = st.text_input("Search bookings", placeholder="Booking or room ID")
        visible_items = items if booking_status == "All" else [b for b in items if b["status"] == booking_status]
        visible_items = search_items(visible_items, query, "id", "room_id", "check_in", "check_out", "status")
        st.caption(f"Showing {len(visible_items)} of {len(items)} bookings")
        booking_rows = [
            {**booking, "payment_status": "PAID" if booking["id"] in paid_booking_ids else "NOT PAID"}
            for booking in visible_items
        ]
        table(booking_rows)
        selected_booking = record_picker(
            visible_items, "Booking details", "booking_quick_detail",
            lambda booking: f"Booking {booking['id']} · {booking['status']} · {booking['check_in']}"
        )
        if selected_booking:
            st.info(f"Room **{selected_booking['room_id']}** · {selected_booking['check_in']} to {selected_booking['check_out']} · total **{inr(selected_booking['total_amount'])}**")
    rooms_path = "/rooms/" if st.session_state.get("is_admin") else "/rooms/available"
    rooms = load(rooms_path, params={"skip": 0, "limit": 100})
    available_rooms = [room for room in (rooms or []) if room["status"] == "AVAILABLE"]
    room_labels = {room_option_label(room): room for room in available_rooms}
    create_tab, edit_tab, cancel_tab, pay_tab = st.tabs(["New booking", "Reschedule", "Cancel booking", "Payments"])
    with create_tab:
        if not room_labels:
            st.info("There are no available rooms to book. Browse Available rooms again later.")
        else:
            labels = list(room_labels)
            preset_room_id = st.session_state.pop("booking_room_id", None)
            if preset_room_id is not None:
                preset_label = next((label for label, room in room_labels.items() if room["id"] == preset_room_id), None)
                if preset_label:
                    st.session_state.booking_create_room = preset_label
            with st.form("booking_create"):
                room_label = st.selectbox("Available room", labels, key="booking_create_room")
                chosen_room = room_labels[room_label]
                st.caption(f"{chosen_room.get('room_type_name', 'Room type')} · capacity {chosen_room.get('capacity', '—')} · {inr(chosen_room['price_per_night']) if chosen_room.get('price_per_night') is not None else 'price set by hotel'} per night")
                check_in = st.date_input("Check-in", value=date.today() + timedelta(days=1))
                check_out = st.date_input("Check-out", value=date.today() + timedelta(days=2))
                submit = st.form_submit_button("Create booking", type="primary")
            if submit:
                changed("POST", "/bookings/", {"room_id": chosen_room["id"], "check_in": check_in.isoformat(), "check_out": check_out.isoformat()}, success="Booking created.")
    if items:
        confirmed = [item for item in items if item["status"] == "CONFIRMED"]
        if confirmed:
            booking_map = {f"Booking {b['id']} · room {b['room_id']} · {b['check_in']} to {b['check_out']}": b for b in confirmed}
            with edit_tab:
                label = st.selectbox("Booking to reschedule", list(booking_map), key="booking_edit_select")
                booking = booking_map[label]
                available_labels = list(room_labels)
                if not available_labels:
                    st.info("No available rooms can be selected for this reschedule.")
                else:
                    selected_label = next((label for label, room in room_labels.items() if room["id"] == booking["room_id"]), available_labels[0])
                    with st.form("booking_edit"):
                        room_label = st.selectbox("Available room", available_labels, index=available_labels.index(selected_label))
                        check_in = st.date_input("Check-in", value=date.fromisoformat(booking["check_in"]))
                        check_out = st.date_input("Check-out", value=date.fromisoformat(booking["check_out"]))
                        submit = st.form_submit_button("Save new dates")
                    if submit:
                        changed("PUT", f"/bookings/{booking['id']}", {"room_id": room_labels[room_label]["id"], "check_in": check_in.isoformat(), "check_out": check_out.isoformat()}, success="Booking updated.")
            with cancel_tab:
                label = st.selectbox("Booking to cancel", list(booking_map), key="booking_cancel_select")
                st.caption("Cancellation retains the booking record for history.")
                if st.button("Cancel selected booking", type="primary"):
                    changed("PATCH", f"/bookings/{booking_map[label]['id']}/cancel", success="Booking cancelled.")
        else:
            st.info("There are no confirmed bookings to update or cancel.")

    with pay_tab:
        payable = [booking for booking in (items or []) if booking["status"] == "CONFIRMED" and booking["id"] not in paid_booking_ids]
        if payable:
            booking_options = {
                f"Booking {booking['id']} · room {booking['room_id']} · {inr(booking['total_amount'])}": booking
                for booking in payable
            }
            with st.form("booking_payment"):
                booking_label = st.selectbox("Confirmed booking", list(booking_options))
                booking = booking_options[booking_label]
                st.write(f"Amount due: **{inr(booking['total_amount'])}**")
                method = st.selectbox("Payment method", ["Card", "Cash", "Bank transfer", "Other"])
                submit = st.form_submit_button("Record payment", type="primary")
            if submit:
                changed("POST", "/payments/", {"booking_id": booking["id"], "amount": str(booking["total_amount"]), "payment_method": method}, success="Payment recorded.")
        else:
            st.info("No unpaid confirmed bookings are available for payment.")
        st.caption("Payments are shown with your bookings. The API does not provide payment editing, deletion, or refunds.")


def employee_bookings_page():
    st.title("Booking operations")
    st.caption("You can review and update guest bookings. Payment and guest account details are not available in this workspace.")
    items = load("/bookings/", params={"skip": 0, "limit": 100})
    if items is None:
        return
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        status_filter = st.selectbox("Booking status", ["All", "CONFIRMED", "CANCELLED"])
    with search_col:
        query = st.text_input("Search bookings", placeholder="Booking, room, or guest ID")
    visible = items if status_filter == "All" else [item for item in items if item["status"] == status_filter]
    visible = search_items(visible, query, "id", "user_id", "room_id", "check_in", "check_out", "status")
    st.caption(f"Showing {len(visible)} of {len(items)} bookings")
    table(visible, empty="No bookings found.")
    selected = record_picker(
        visible,
        "Booking details",
        "employee_booking_detail",
        lambda item: f"Booking {item['id']} · guest {item['user_id']} · {item['status']} · {item['check_in']}",
    )
    if selected:
        st.info(f"Guest ID **{selected['user_id']}** · Room **{selected['room_id']}** · {selected['check_in']} to {selected['check_out']} · total **{inr(selected['total_amount'])}**")

    confirmed = [item for item in items if item["status"] == "CONFIRMED"]
    if not confirmed:
        st.info("There are no confirmed bookings to update or cancel.")
        return
    booking_map = {
        f"Booking {item['id']} · guest {item['user_id']} · room {item['room_id']} · {item['check_in']} to {item['check_out']}": item
        for item in confirmed
    }
    reschedule_tab, cancel_tab = st.tabs(["Reschedule", "Cancel booking"])
    with reschedule_tab:
        rooms = load("/rooms/available", params={"skip": 0, "limit": 100}) or []
        room_map = {room_option_label(room): room for room in rooms}
        if not room_map:
            st.info("No available rooms can be selected for rescheduling.")
        else:
            label = st.selectbox("Booking to reschedule", list(booking_map), key="employee_reschedule_booking")
            booking = booking_map[label]
            labels = list(room_map)
            with st.form("employee_booking_edit"):
                room_label = st.selectbox("Available room", labels)
                check_in = st.date_input("Check-in", value=date.fromisoformat(booking["check_in"]))
                check_out = st.date_input("Check-out", value=date.fromisoformat(booking["check_out"]))
                submit = st.form_submit_button("Save booking changes", type="primary")
            if submit:
                changed("PUT", f"/bookings/{booking['id']}", {
                    "room_id": room_map[room_label]["id"],
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                }, success="Booking updated.")
    with cancel_tab:
        label = st.selectbox("Booking to cancel", list(booking_map), key="employee_cancel_booking")
        st.caption("Cancellation keeps the booking in history.")
        if st.button("Cancel selected booking", type="primary"):
            changed("PATCH", f"/bookings/{booking_map[label]['id']}/cancel", success="Booking cancelled.")


def employee_rooms_page():
    st.title("Room status")
    st.caption("Review the room inventory and update operational status. Room details and pricing are managed by an administrator.")
    rooms = load("/rooms/", params={"skip": 0, "limit": 100, "sort_by": "room_number", "sort_order": "asc"})
    if rooms is None:
        return
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        status_filter = st.selectbox("Room status", ["All", "AVAILABLE", "MAINTENANCE", "CLEANING"])
    with search_col:
        query = st.text_input("Find a room", placeholder="Room number or floor")
    visible = rooms if status_filter == "All" else [room for room in rooms if room["status"] == status_filter]
    visible = search_items(visible, query, "room_number", "floor", "status")
    st.caption(f"Showing {len(visible)} of {len(rooms)} rooms")
    table(visible, empty="No rooms found.")
    room_map = {f"Room {room['room_number']} · floor {room['floor']} · {room['status']}": room for room in visible}
    if not room_map:
        return
    label = st.selectbox("Room to update", list(room_map), key="employee_room_status_select")
    room = room_map[label]
    statuses = ["AVAILABLE", "MAINTENANCE", "CLEANING"]
    with st.form("employee_room_status"):
        new_status = st.selectbox("Operational status", statuses, index=statuses.index(room["status"]))
        submit = st.form_submit_button("Update room status", type="primary")
    if submit and new_status != room["status"]:
        changed("PATCH", f"/rooms/{room['id']}", {"status": new_status}, success=f"Room {room['room_number']} status updated.")


def payments_page():
    st.title("Payments")
    payments = load("/payments/", params={"skip": 0, "limit": 100})
    if payments is not None:
        filter_col, search_col = st.columns([1, 2])
        with filter_col:
            payment_status = st.selectbox("Payment status", ["All", "PAID", "PENDING", "FAILED"])
        with search_col:
            query = st.text_input("Search payments", placeholder="Payment, booking, or method")
        visible_payments = payments if payment_status == "All" else [p for p in payments if p["status"] == payment_status]
        visible_payments = search_items(visible_payments, query, "id", "booking_id", "payment_method", "status", "amount")
        st.caption(f"Showing {len(visible_payments)} of {len(payments)} payments")
        table(visible_payments)
        selected_payment = record_picker(
            visible_payments, "Payment details", "payment_quick_detail",
            lambda payment: f"Payment {payment['id']} · booking {payment['booking_id']} · {payment['status']}"
        )
        if selected_payment:
            st.info(f"Amount **{inr(selected_payment['amount'])}** · method {selected_payment['payment_method']} · paid at {selected_payment['paid_at'] or 'not paid'}")
    bookings = load("/bookings/", params={"skip": 0, "limit": 100})
    payable = [b for b in (bookings or []) if b["status"] == "CONFIRMED" and not any(p["booking_id"] == b["id"] and p["status"] == "PAID" for p in (payments or []))]
    st.subheader("Record a payment")
    if payable:
        booking_options = {f"Booking {b['id']} · {b['total_amount']} · {b['check_in']} to {b['check_out']}": b for b in payable}
        with st.form("payment_create"):
            label = st.selectbox("Booking", list(booking_options))
            booking = booking_options[label]
            st.write(f"Amount due: **{inr(booking['total_amount'])}**")
            amount = st.text_input("Amount (₹)", value=str(booking["total_amount"]))
            method = st.selectbox("Payment method", ["Card", "Cash", "Bank transfer", "Other"])
            submit = st.form_submit_button("Record payment")
        if submit:
            try:
                parsed_amount = Decimal(amount)
                if parsed_amount <= 0:
                    raise InvalidOperation
                changed("POST", "/payments/", {"booking_id": booking["id"], "amount": str(parsed_amount), "payment_method": method}, success="Payment recorded.")
            except (InvalidOperation, ValueError):
                st.error("Enter a valid positive amount.")
    else:
        st.info("No unpaid confirmed bookings are available for payment.")
    st.caption("Payments are read-only after creation; the API does not provide update, delete, or refund operations.")


def users_page():
    st.title("User management")
    st.caption("This screen requires an ADMIN account. User edits and deletion also require the configured main administrator.")
    users = load("/admin/users")
    role_records = load("/admin/user-roles")
    role_by_id = {record["user_id"]: record["role"] for record in (role_records or [])}
    if users is not None:
        query = st.text_input("Find a user", placeholder="Name, username, or email")
        visible_users = search_items(users, query, "id", "full_name", "username", "email")
        st.caption(f"Showing {len(visible_users)} of {len(users)} users")
        table([{**user, "role": role_by_id.get(user["id"], "USER")} for user in visible_users])
    if users:
        user_map = {f"{u['full_name']} · {u['username']} (ID {u['id']})": u for u in visible_users}
        edit_tab, reset_tab, delete_tab, role_tab = st.tabs(["Edit user", "Reset password", "Delete user", "Access role"])
        with edit_tab:
            label = st.selectbox("Select user", list(user_map), key="user_edit_select")
            user = user_map[label]
            with st.form("user_edit"):
                username = st.text_input("Username", value=user["username"], max_chars=50)
                email = st.text_input("Email", value=user["email"])
                full_name = st.text_input("Full name", value=user["full_name"], max_chars=100)
                submit = st.form_submit_button("Save changes")
            if submit:
                changed("PUT", f"/admin/users/{user['id']}", {"username": username, "email": email, "full_name": full_name}, success="User updated.")
        with reset_tab:
            st.warning("This replaces the account password. The API stores only its hash; the current password cannot be viewed.")
            with st.form("user_password_reset"):
                new_password = st.text_input("New password (at least 8 characters)", type="password", key="reset_user_password")
                confirm_password = st.text_input("Confirm new password", type="password", key="confirm_reset_user_password")
                submit = st.form_submit_button("Reset password", type="primary")
            if submit:
                if new_password != confirm_password:
                    st.error("The passwords do not match.")
                elif len(new_password) < 8:
                    st.error("The password must contain at least 8 characters.")
                else:
                    changed(
                        "PUT",
                        f"/admin/users/{user['id']}/password",
                        {"password": new_password},
                        success=f"Password reset for {user['username']}. Share the new password with them securely.",
                    )
        with delete_tab:
            label = st.selectbox("User to delete", list(user_map), key="user_delete_select")
            st.warning("Users with booking history cannot be deleted. The API does not provide an administrator-only user creation endpoint; new accounts use registration.")
            if st.button("Delete selected user", type="primary"):
                changed("DELETE", f"/admin/users/{user_map[label]['id']}", success="User deleted.")
        with role_tab:
            st.caption("Registration creates standard users. Assign employee access here; the configured main administrator cannot be demoted here.")
            eligible_users = [user for user in visible_users if role_by_id.get(user["id"], "USER") != "ADMIN"]
            if not eligible_users:
                st.info("No non-administrator accounts match the current search.")
            else:
                role_targets = {
                    f"{user['full_name']} · {user['username']} (ID {user['id']})": user
                    for user in eligible_users
                }
                role_label = st.selectbox("Account", list(role_targets), key="role_target_select")
                role_user = role_targets[role_label]
                current_role = role_by_id.get(role_user["id"], "USER")
                role_options = ["USER", "EMPLOYEE"]
                with st.form("user_role_update"):
                    new_role = st.selectbox("Access level", role_options, index=role_options.index(current_role))
                    role_submit = st.form_submit_button("Save access level", type="primary")
                if role_submit and new_role != current_role:
                    changed(
                        "PUT",
                        f"/admin/users/{role_user['id']}/role",
                        {"role": new_role},
                        success=f"{role_user['username']} access changed to {new_role.lower()}.",
                    )


def audit_page():
    st.title("Audit log")
    items = load("/audit-logs/", params={"skip": 0, "limit": 100})
    if items is not None:
        filter_col, search_col = st.columns([1, 2])
        with filter_col:
            actions = ["All"] + sorted({item["action"] for item in items})
            action = st.selectbox("Action", actions)
        with search_col:
            query = st.text_input("Search audit records", placeholder="Entity or ID")
        visible_items = items if action == "All" else [item for item in items if item["action"] == action]
        visible_items = search_items(visible_items, query, "entity", "entity_id", "user_id", "old_value", "new_value")
        st.caption(f"Showing {len(visible_items)} of {len(items)} audit records")
        table(visible_items)


def go_to_page(page: str):
    st.session_state.pending_navigation = page
    st.rerun()


PAGE_ICONS = {
    "Welcome": "🏠",
    "Live dashboard": "📊",
    "Available rooms": "🛏️",
    "Bookings": "📅",
    "Payments": "💳",
    "Rooms": "🧹",
    "Room types": "🛌",
    "User management": "👥",
    "Audit log": "🧾",
}


def navigation_button(page: str, active_page: str):
    button_type = "primary" if page == active_page else "secondary"
    if st.button(
        f"{PAGE_ICONS.get(page, '•')}  {page}",
        key=f"nav_{page.lower().replace(' ', '_')}",
        type=button_type,
        use_container_width=True,
    ):
        go_to_page(page)


def welcome_page(is_admin: bool, is_employee: bool = False):
    username = st.session_state.get("username", "there")
    st.title(f"Welcome, {username}")
    st.caption("Hotel Booking & Room Management")

    if is_admin:
        st.subheader("Administrator access")
        st.write("You help keep hotel inventory accurate and operations organized.")
        with st.container(border=True):
            st.markdown("**Your responsibilities**")
            st.markdown(
                "- Keep room types, room numbers, floors, and room statuses up to date.\n"
                "- Review audit records when you need to understand changes.\n"
                "- Protect guest information and only make changes needed for hotel operations.\n"
                "- Bookings and payments remain scoped to your own account. User edits, deletion, and password resets are limited to the configured main administrator."
            )
    elif is_employee:
        st.subheader("Employee access")
        st.write("Help guests by keeping bookings accurate and room operations up to date.")
        with st.container(border=True):
            st.markdown("**Your responsibilities**")
            st.markdown(
                "- Review guest bookings and reschedule or cancel them when needed.\n"
                "- Keep room operational statuses current: Available, Maintenance, or Cleaning.\n"
                "- Protect guest booking information. Payment records, room pricing, user accounts, and audit logs are restricted to administrators."
            )
    else:
        st.subheader("Standard account access")
        st.write("Use this account to browse available rooms and manage your own bookings.")
        with st.container(border=True):
            st.markdown("**Your responsibilities**")
            st.markdown(
                "- Check your room and stay dates before confirming a booking.\n"
                "- Update or cancel your own bookings promptly when plans change.\n"
                "- Keep your sign-in details private. Room inventory and other users are managed by administrators."
            )

    st.subheader("Choose where to go")
    st.caption("Use the section buttons in the sidebar or the floating Quick actions menu to move around.")
    left, right = st.columns(2)
    with left:
        first_page = "My bookings" if is_admin else "Booking operations" if is_employee else "Browse available rooms"
        first_target = "Bookings" if is_admin or is_employee else "Available rooms"
        if st.button(first_page, use_container_width=True, type="primary"):
            go_to_page(first_target)
    with right:
        second_label = "Room status" if is_employee else "My bookings" if not is_admin else "My payments"
        second_target = "Rooms" if is_employee else "Bookings" if not is_admin else "Payments"
        if st.button(second_label, use_container_width=True):
            go_to_page(second_target)
    if is_admin:
        admin_left, admin_right = st.columns(2)
        with admin_left:
            if st.button("Manage rooms", use_container_width=True):
                go_to_page("Rooms")
        with admin_right:
            if st.button("Manage room types", use_container_width=True):
                go_to_page("Room types")


def live_dashboard(is_admin: bool):
    st.title("Live dashboard")
    st.write("This summary loads only when you open it. Use refresh to fetch the latest records.")
    if st.button("↻ Refresh dashboard", type="primary"):
        st.rerun()
    try:
        result = api_request("GET", "/")
        bookings = api_request("GET", "/bookings/", params={"skip": 0, "limit": 100})
        payments = api_request("GET", "/payments/", params={"skip": 0, "limit": 100})
        st.success(result.get("message", "API connected"))
        confirmed = [booking for booking in bookings if booking["status"] == "CONFIRMED"]
        paid = [payment for payment in payments if payment["status"] == "PAID"]
        metrics = st.columns(4)
        metrics[0].metric("My bookings", len(bookings))
        metrics[1].metric("Confirmed", len(confirmed))
        metrics[2].metric("Payments", len(payments))
        metrics[3].metric("Paid total", inr(sum((Decimal(payment['amount']) for payment in paid), Decimal('0'))))
        st.subheader("Upcoming stays")
        upcoming = [booking for booking in confirmed if date.fromisoformat(booking["check_out"]) >= date.today()]
        upcoming.sort(key=lambda booking: booking["check_in"])
        if upcoming:
            table(upcoming[:5])
        else:
            st.info("No upcoming confirmed stays.")
        if is_admin:
            rooms = api_request("GET", "/rooms/", params={"skip": 0, "limit": 100})
            available = sum(room["status"] == "AVAILABLE" for room in rooms)
            st.metric("Available rooms", available)
    except APIError as exc:
        show_error(exc)


def main():
    if target := st.session_state.pop("pending_navigation", None):
        st.session_state.navigation_page = target
    if "api_url" not in st.session_state:
        st.session_state.api_url = DEFAULT_API_URL
    if not st.session_state.get("token"):
        with st.sidebar:
            st.header("Connection")
            st.text_input("FastAPI base URL", key="api_url")
            st.caption("Default: http://127.0.0.1:8000")
            if st.button("Check API"):
                try:
                    result = api_request("GET", "/")
                    st.success(result.get("message", "API is responding"))
                except APIError as exc:
                    show_error(exc)
        login_screen()
        return

    if "role" not in st.session_state:
        try:
            profile = api_request("GET", "/auth/me")
            roles = {str(role).upper() for role in profile.get("roles", [])}
            if "ADMIN" in roles:
                st.session_state.role = "ADMIN"
            elif roles.intersection({"EMPLOYEE", "RECEPTIONIST"}):
                st.session_state.role = "EMPLOYEE"
            else:
                st.session_state.role = "USER"
            st.session_state.username = profile.get("username", st.session_state.get("username", "user"))
            st.session_state.is_admin = st.session_state.role == "ADMIN"
            st.session_state.is_employee = st.session_state.role == "EMPLOYEE"
        except APIError as exc:
            show_error(exc)
            return

    if st.session_state.is_admin:
        pages = ["Welcome", "Live dashboard", "Rooms", "Room types", "Available rooms", "Bookings", "Payments", "User management", "Audit log"]
    elif st.session_state.get("is_employee"):
        pages = ["Welcome", "Available rooms", "Bookings", "Rooms"]
    else:
        pages = ["Welcome", "Available rooms", "Bookings"]
    admin_pages = {"Live dashboard", "Payments", "Room types", "User management", "Audit log"}
    if "navigation_page" not in st.session_state:
        st.session_state.navigation_page = "Welcome"
    elif st.session_state.navigation_page not in pages:
        st.session_state.navigation_page = "Welcome"

    st.markdown(
        """<style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #20232d 0%, #282b36 58%, #22252e 100%);
            border-right: 1px solid rgba(255,255,255,.07);
        }
        [data-testid="stSidebar"] > div:first-child { padding: 1.2rem .9rem 1.5rem; }
        [data-testid="stSidebar"] h2 { font-size: 1.18rem; letter-spacing: -.02em; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #aeb3c1; }
        [data-testid="stSidebar"] [data-testid="stTextInput"] input {
            border: 1px solid rgba(255,255,255,.1); border-radius: 11px;
            background: rgba(10,12,18,.62);
        }
        [data-testid="stSidebar"] .stButton > button {
            min-height: 2.7rem; border-radius: 12px; font-weight: 550;
            border-color: rgba(255,255,255,.12); transition: transform .16s ease, box-shadow .16s ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            transform: translateX(3px); border-color: rgba(255,255,255,.3);
            box-shadow: 0 5px 16px rgba(0,0,0,.18);
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            box-shadow: 0 6px 18px rgba(255,75,80,.22);
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            border: 1px solid rgba(255,255,255,.1); border-radius: 13px;
            background: rgba(255,255,255,.025);
        }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.1); }
        .hotel-brand { display:flex; align-items:center; gap:.7rem; margin:.2rem 0 1.15rem; }
        .hotel-brand-mark { display:grid; place-items:center; width:2.5rem; height:2.5rem;
            border-radius:12px; background:linear-gradient(145deg,#ff696e,#e83f4c);
            box-shadow:0 5px 16px rgba(255,75,80,.25); font-size:1.2rem; }
        .hotel-brand-name { font-size:1.08rem; font-weight:750; letter-spacing:-.025em; color:#fff; }
        .hotel-brand-caption { margin-top:.05rem; color:#aeb3c1; font-size:.75rem; }
        .st-key-sidebar_profile { padding:.8rem .85rem; margin:.3rem 0 1rem;
            background:rgba(255,255,255,.055); border:1px solid rgba(255,255,255,.08);
            border-radius:14px; }
        .st-key-sidebar_profile p { margin:0; }
        </style>""",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown(
            '<div class="hotel-brand"><div class="hotel-brand-mark">🏨</div>'
            '<div><div class="hotel-brand-name">Hotel Manager</div>'
            '<div class="hotel-brand-caption">Booking & room services</div></div></div>',
            unsafe_allow_html=True,
        )
        with st.container(key="sidebar_profile"):
            st.caption("SIGNED IN AS")
            st.markdown(f"**{st.session_state.get('username', 'user')}**")
            account_label = "🛡️ Administrator" if st.session_state.is_admin else "🧑‍💼 Employee" if st.session_state.get("is_employee") else "👤 Guest account"
            st.caption(account_label)
        with st.expander("⚙️ API connection"):
            st.text_input("FastAPI base URL", key="api_url")
            st.caption("Default: http://127.0.0.1:8000")
        st.markdown("**YOUR WORKSPACE**")
        if st.session_state.is_admin:
            workspace_pages = ["Welcome", "Live dashboard", "Available rooms", "Bookings", "Payments"]
        elif st.session_state.get("is_employee"):
            workspace_pages = ["Welcome", "Available rooms", "Bookings", "Rooms"]
        else:
            workspace_pages = ["Welcome", "Available rooms", "Bookings"]
        for nav_page in workspace_pages:
            navigation_button(nav_page, st.session_state.navigation_page)
        if st.session_state.is_admin:
            st.divider()
            with st.expander("Administration", expanded=st.session_state.navigation_page in admin_pages):
                for nav_page in ["Rooms", "Room types", "User management", "Audit log"]:
                    navigation_button(nav_page, st.session_state.navigation_page)
        if st.button("Sign out", use_container_width=True):
            st.session_state.pop("token", None)
            st.session_state.pop("username", None)
            st.session_state.pop("is_admin", None)
            st.session_state.pop("is_employee", None)
            st.session_state.pop("role", None)
            st.session_state.pop("navigation_page", None)
            st.rerun()

    page = st.session_state.navigation_page

    if message := st.session_state.pop("flash_message", None):
        st.toast(message, icon="✅")

    st.markdown(
        """<style>
        .st-key-floating_action_menu {
            position: fixed;
            right: 1.4rem;
            bottom: 1.4rem;
            width: fit-content;
            z-index: 1000;
        }
        .st-key-floating_action_menu button {
            box-shadow: 0 5px 18px rgba(20, 35, 70, 0.22);
            border-radius: 999px;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    with st.container(key="floating_action_menu"):
        with st.popover("⚡ Quick actions", type="primary", key="floating_quick_actions", use_container_width=True):
            st.caption("Open a workspace")
            if st.session_state.is_admin:
                quick_pages = ["Live dashboard", "Available rooms", "Bookings", "Payments", "Rooms", "Room types", "User management", "Audit log"]
            elif st.session_state.get("is_employee"):
                quick_pages = ["Available rooms", "Bookings", "Rooms"]
            else:
                quick_pages = ["Available rooms", "Bookings"]
            for quick_page in quick_pages:
                if st.button(quick_page, key=f"quick_{quick_page}", use_container_width=True):
                    go_to_page(quick_page)

    if page in admin_pages and not st.session_state.is_admin:
        st.title(page)
        st.warning("This screen is available to administrator accounts.")
        st.info("Your account does not have administrator access. Your workspace includes only the pages assigned to your role. Contact your hotel administrator if you need access.")
        return

    if page == "Welcome":
        welcome_page(st.session_state.is_admin, st.session_state.get("is_employee", False))
    elif page == "Live dashboard":
        live_dashboard(st.session_state.is_admin)
    elif page == "Available rooms":
        available_rooms_page()
    elif page == "Rooms":
        employee_rooms_page() if st.session_state.get("is_employee") and not st.session_state.is_admin else rooms_page()
    elif page == "Room types":
        room_types_page()
    elif page == "Bookings":
        bookings_page()
    elif page == "Payments":
        payments_page()
    elif page == "User management":
        users_page()
    elif page == "Audit log":
        audit_page()


main()
