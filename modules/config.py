"""Static configuration and constants for the Hotel Analytics app."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

BASE_CSV = DATA_DIR / "hotel_bookings.csv"        # the supplied dataset
ADDED_CSV = DATA_DIR / "added_bookings.csv"       # bookings created inside the app
USERS_JSON = DATA_DIR / "users.json"
SETTINGS_JSON = DATA_DIR / "settings.json"
REMEMBER_JSON = DATA_DIR / "remember_me.json"
MODEL_FILE = MODEL_DIR / "cancel_model.joblib"

APP_NAME = "Hotel Analytics"
APP_TAGLINE = "Cancellation & Revenue Management"
RECOVERY_KEY = "HOTEL-RESET-2024"   # used by the "Forgot password?" flow

DEFAULT_SETTINGS = {
    "hotel_name": "Hotel Analytics",
    "eur_to_inr": 90.0,          # dataset ADR is in EUR -> shown in INR
    "low_risk_max": 30,          # % below -> Low risk
    "high_risk_min": 60,         # % above -> High risk
    "window_months": 12,         # default analysis window (months)
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS)}
MONTH_ABBR = [m[:3] for m in MONTHS]

# Market segment names used in the dashboard
SEGMENT_LABELS = {
    "Online TA": "Online Travel Agency",
    "Offline TA/TO": "Travel Agent",
    "Direct": "Direct",
    "Corporate": "Corporate",
    "Groups": "Groups",
    "Complementary": "Complementary",
    "Aviation": "Aviation",
    "Undefined": "Undefined",
}
SEGMENT_REVERSE = {v: k for k, v in SEGMENT_LABELS.items()}

# The dataset anonymises rooms as letters A-L. They are grouped into the four
# room categories used in the dashboard.
ROOM_GROUPS = {
    "A": "Standard", "B": "Standard",
    "C": "Deluxe", "D": "Deluxe",
    "E": "Suite", "F": "Suite",
    "G": "Family", "H": "Family", "I": "Family", "K": "Family", "L": "Family", "P": "Family",
}
ROOM_ORDER = ["Standard", "Deluxe", "Suite", "Family"]
ROOM_COLORS = {"Standard": "#7c6cf0", "Deluxe": "#3aa7ff", "Suite": "#3ecf8e", "Family": "#ffa94d"}

COUNTRY_NAMES = {
    "PRT": "Portugal", "GBR": "United Kingdom", "FRA": "France", "ESP": "Spain", "DEU": "Germany",
    "ITA": "Italy", "IRL": "Ireland", "BEL": "Belgium", "BRA": "Brazil", "NLD": "Netherlands",
    "USA": "United States", "CHE": "Switzerland", "AUT": "Austria", "CN": "China", "CHN": "China",
    "SWE": "Sweden", "POL": "Poland", "ISR": "Israel", "RUS": "Russia", "NOR": "Norway",
    "ROU": "Romania", "FIN": "Finland", "DNK": "Denmark", "AUS": "Australia", "IND": "India",
    "ARG": "Argentina", "LUX": "Luxembourg", "TUR": "Turkey", "CHL": "Chile", "JPN": "Japan",
    "KOR": "South Korea", "MEX": "Mexico", "CAN": "Canada", "GRC": "Greece", "UKR": "Ukraine",
}

# Colours
TEAL = "#0f9d92"
TEAL_DARK = "#0b6f68"
BLUE = "#4da3ff"
PINK = "#ff6b9a"
PURPLE = "#8b6cf0"
GREEN = "#2ecc9a"
ORANGE = "#ffa94d"
RED = "#ef4b5f"
