"""Pydantic schemas for Hotel Analytics API."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    name: str
    email: str
    password: str
    role: Optional[str] = "User"

class PasswordChangeRequest(BaseModel):
    new_password: str

class UserProfile(BaseModel):
    username: str
    name: str
    email: str
    role: str

class LoginResponse(BaseModel):
    token: str
    user: UserProfile

class ResetPasswordRequest(BaseModel):
    identifier: str
    recovery_key: str
    new_password: str

class SettingsSchema(BaseModel):
    hotel_name: str = "Hotel Analytics"
    eur_to_inr: float = 90.0
    eur_to_usd: float = 1.08
    currency: str = "INR"
    low_risk_max: float = 30.0
    high_risk_min: float = 60.0
    window_months: int = 12

class BookingInput(BaseModel):
    guest_name: str = "Guest"
    hotel: str = "City Hotel"
    lead_time: int = 30
    arrival_date_year: Optional[int] = None
    arrival_date_month: str = "August"
    arrival_date_week_number: Optional[int] = 32
    arrival_date_day_of_month: int = 15
    stays_in_weekend_nights: int = 1
    stays_in_week_nights: int = 2
    adults: int = 2
    children: float = 0.0
    babies: float = 0.0
    meal: str = "BB"
    country: str = "PRT"
    market_segment: str = "Online TA"
    distribution_channel: str = "TA/TO"
    is_repeated_guest: int = 0
    previous_cancellations: int = 0
    previous_bookings_not_canceled: int = 0
    reserved_room_type: str = "A"
    assigned_room_type: Optional[str] = "A"
    booking_changes: int = 0
    deposit_type: str = "No Deposit"
    days_in_waiting_list: int = 0
    customer_type: str = "Transient"
    adr: float = 120.0
    required_car_parking_spaces: int = 0
    total_of_special_requests: int = 1
    agent: Optional[str] = "9"
    company: Optional[str] = "NULL"

class RiskDriver(BaseModel):
    feature: str
    impact: float

class PredictionResponse(BaseModel):
    probability: float
    probability_pct: float
    risk_level: str
    revenue_at_risk: float
    currency_symbol: str
    drivers: List[RiskDriver]
    recommendations: List[str]

class BookingRecord(BaseModel):
    booking_id: str
    guest_name: str
    hotel: str
    arrival_date: str
    stays_in_weekend_nights: int
    stays_in_week_nights: int
    total_nights: int
    adults: int
    children: float
    room_group: str
    market_segment: str
    deposit_type: str
    adr: float
    revenue: float
    reservation_status: str
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    created_at: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str

class ForecastPoint(BaseModel):
    month: str
    forecast: float
    lower: float
    upper: float

class ForecastResponse(BaseModel):
    metric: str
    horizon: int
    data: List[ForecastPoint]
    seasonal_index: Dict[str, float]

