"""FastAPI router endpoints for Hotel Analytics."""
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import Optional, List, Dict, Any

from modules import auth
from backend.schemas import (
    LoginRequest, RegisterRequest, PasswordChangeRequest, LoginResponse, UserProfile, ResetPasswordRequest,
    SettingsSchema, BookingInput, PredictionResponse, StatusUpdate
)
from backend.services import service
from backend.auth_jwt import create_access_token, get_current_user, require_admin

router = APIRouter(prefix="/api")

# ----------------------------------------------------------------------------- Auth
@router.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    auth_res = auth.authenticate(req.username_or_email, req.password)
    if not auth_res:
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
    username, udata = auth_res
    token = create_access_token(udata)
    return LoginResponse(
        token=token,
        user=UserProfile(
            username=username,
            name=udata.get("name", username.title()),
            email=udata.get("email", ""),
            role=udata.get("role", "User")
        )
    )

@router.post("/auth/register", response_model=LoginResponse)
def register(req: RegisterRequest):
    username = req.username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    
    role = req.role if req.role in ("User", "Administrator") else "User"
    ok, msg = auth.add_user(username, req.name, req.email, role, req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    
    auth_res = auth.authenticate(username, req.password)
    if not auth_res:
        raise HTTPException(status_code=500, detail="Failed to initialize user session")
    
    uname, udata = auth_res
    token = create_access_token(udata)
    return LoginResponse(
        token=token,
        user=UserProfile(
            username=uname,
            name=udata.get("name", uname.title()),
            email=udata.get("email", ""),
            role=udata.get("role", "User")
        )
    )

@router.get("/auth/me", response_model=UserProfile)
def get_me(user: dict = Depends(get_current_user)):
    return UserProfile(
        username=user.get("sub", "guest"),
        name=user.get("name", "User"),
        email=user.get("email", ""),
        role=user.get("role", "User")
    )

@router.post("/auth/reset-password")
def reset_pwd(req: ResetPasswordRequest):
    ok, msg = auth.reset_password(req.identifier, req.recovery_key, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

# ----------------------------------------------------------------------------- Analytics
@router.get("/analytics/kpis")
def get_kpis(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    hotel: Optional[str] = Query("All", description="Hotel filter: All, City Hotel, Resort Hotel")
):
    return service.get_kpis(start_date, end_date, hotel)

@router.get("/analytics/trend")
def get_trend(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    hotel: Optional[str] = Query("All")
):
    return service.get_trend(start_date, end_date, hotel)

@router.get("/analytics/segments")
def get_segments(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    hotel: Optional[str] = Query("All")
):
    return service.get_segments(start_date, end_date, hotel)

@router.get("/analytics/rooms")
def get_rooms(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    hotel: Optional[str] = Query("All")
):
    return service.get_rooms(start_date, end_date, hotel)

@router.get("/analytics/channels")
def get_channels(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    hotel: Optional[str] = Query("All")
):
    return service.get_channels(start_date, end_date, hotel)

@router.get("/analytics/cancellation-drivers")
def get_cancellation_drivers(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    hotel: Optional[str] = Query("All")
):
    return service.get_cancellation_drivers(start_date, end_date, hotel)

@router.get("/analytics/geography")
def get_geography(limit: int = Query(15, ge=1, le=50)):
    return service.get_geography(limit)

@router.get("/analytics/forecast")
def get_forecast(
    metric: str = Query("net_bookings", description="net_bookings, revenue, adr, room_nights, bookings, cancelled"),
    horizon: int = Query(6, ge=1, le=12),
    scenario_pct: float = Query(0.0, ge=-50.0, le=50.0),
    hotel: Optional[str] = Query("All")
):
    return service.get_forecast(metric, horizon, scenario_pct, hotel)

# ----------------------------------------------------------------------------- Machine Learning
@router.post("/ml/predict", response_model=PredictionResponse)
def predict_risk(booking: BookingInput):
    return service.predict_risk(booking)

@router.get("/ml/diagnostics")
def get_diagnostics():
    return service.get_model_diagnostics()

@router.post("/ml/retrain")
def retrain_model(user: dict = Depends(require_admin)):
    bundle = service.get_model_bundle(force_retrain=True)
    m = bundle.get("metrics", {})
    return {
        "success": True,
        "trained_at": bundle.get("trained_at"),
        "rows": bundle.get("n_rows"),
        "accuracy": round(float(m.get("accuracy", 0)), 3),
        "auc": round(float(m.get("auc", 0)), 3)
    }

# ----------------------------------------------------------------------------- Bookings CRUD
@router.get("/bookings")
def list_bookings(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    hotel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None)
):
    return service.list_bookings(limit, offset, search, hotel, status, risk_level)

@router.post("/bookings")
def create_booking(booking: BookingInput, user: dict = Depends(get_current_user)):
    user_name = user.get("name", "User")
    return service.add_booking(booking, user_name=user_name)

@router.patch("/bookings/{booking_id}/status")
def update_status(booking_id: str, update: StatusUpdate, user: dict = Depends(get_current_user)):
    ok = service.update_booking_status(booking_id, update.status)
    if not ok:
        raise HTTPException(status_code=404, detail="Booking not found or cannot be updated")
    return {"success": True, "booking_id": booking_id, "new_status": update.status}

# ----------------------------------------------------------------------------- Settings & Users
@router.get("/settings")
def get_settings():
    return service.get_settings()

@router.post("/settings")
def save_settings(new_settings: SettingsSchema, user: dict = Depends(require_admin)):
    return service.update_settings(new_settings.model_dump())

@router.get("/settings/users")
def list_users(user: dict = Depends(require_admin)):
    raw = auth.load_users()
    clean = []
    for uname, u in raw.items():
        clean.append({
            "username": uname,
            "name": u.get("name", uname.title()),
            "email": u.get("email", ""),
            "role": u.get("role", "User")
        })
    return clean

@router.post("/settings/users")
def create_user_by_admin(req: RegisterRequest, user: dict = Depends(require_admin)):
    ok, msg = auth.add_user(req.username, req.name, req.email, req.role or "User", req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@router.delete("/settings/users/{username}")
def remove_user(username: str, user: dict = Depends(require_admin)):
    if username.lower() == user.get("sub", "").lower():
        raise HTTPException(status_code=400, detail="You cannot delete the account you are currently logged in with")
    ok, msg = auth.delete_user(username)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@router.put("/settings/users/{username}/password")
def change_password(username: str, req: PasswordChangeRequest, user: dict = Depends(require_admin)):
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    ok = auth.set_password(username, req.new_password)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "message": "Password updated successfully"}

# ----------------------------------------------------------------------------- Reports & Export
@router.get("/reports/export")
def export_report(dataset: str = Query("bookings")):
    data = service.export_data(dataset)
    filename = f"hotel_{dataset}_{service.get_settings().get('hotel_name', 'analytics')}.csv"
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

