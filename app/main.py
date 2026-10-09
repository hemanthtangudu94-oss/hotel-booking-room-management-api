from fastapi import FastAPI


#connecting core to main
from app.core.logging import setup_logging


#connecting routues to main
from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.room_types import router as room_type_router
from app.api.routes.rooms import router as room_router
from app.api.routes.bookings import router as booking_router
from app.api.routes.payments import router as payment_router
from app.api.routes.audit_logs import router as audit_log_router


setup_logging()



app = FastAPI(
    title="Hotel Booking & Room Management API",
    description="Production-grade hotel booking and room management backend",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(room_type_router)
app.include_router(room_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(audit_log_router)


@app.get("/")
def root():
    return {
        "message": "Hotel Booking API is Running Successfully"
    }