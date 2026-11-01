"""Dataset loading, cleaning and feature engineering (no Streamlit dependency)."""
import uuid
from datetime import datetime

import numpy as np
import pandas as pd

from . import config

BASE_COLUMNS = [
    "hotel", "is_canceled", "lead_time", "arrival_date_year", "arrival_date_month",
    "arrival_date_week_number", "arrival_date_day_of_month", "stays_in_weekend_nights",
    "stays_in_week_nights", "adults", "children", "babies", "meal", "country", "market_segment",
    "distribution_channel", "is_repeated_guest", "previous_cancellations",
    "previous_bookings_not_canceled", "reserved_room_type", "assigned_room_type",
    "booking_changes", "deposit_type", "agent", "company", "days_in_waiting_list",
    "customer_type", "adr", "required_car_parking_spaces", "total_of_special_requests",
    "reservation_status", "reservation_status_date",
]
EXTRA_COLUMNS = ["booking_id", "guest_name", "risk_score", "risk_level", "created_by", "created_at"]


def file_signature(path) -> str:
    try:
        st = path.stat()
        return f"{st.st_mtime_ns}-{st.st_size}"
    except FileNotFoundError:
        return "none"


def read_base() -> pd.DataFrame:
    return pd.read_csv(config.BASE_CSV)


def read_added() -> pd.DataFrame:
    if config.ADDED_CSV.exists():
        try:
            return pd.read_csv(config.ADDED_CSV)
        except Exception:
            pass
    return pd.DataFrame(columns=BASE_COLUMNS + EXTRA_COLUMNS)


def preprocess(df: pd.DataFrame, rate: float, source: str) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df
    df["children"] = df["children"].fillna(0)
    df["country"] = df["country"].fillna("Unknown")
    df["adr"] = df["adr"].astype(float).clip(0, 1000)          # remove -6.38 and 5400 outliers
    month_num = df["arrival_date_month"].map(config.MONTH_NUM)
    df["arrival_date"] = pd.to_datetime(dict(
        year=df["arrival_date_year"], month=month_num, day=df["arrival_date_day_of_month"]))
    df["month_start"] = df["arrival_date"].dt.to_period("M").dt.to_timestamp()
    df["month_num"] = month_num
    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    stay_value = df["adr"] * df["total_nights"] * rate
    canceled = df["is_canceled"] == 1
    df["revenue"] = np.where(canceled, 0.0, stay_value)
    df["lost_revenue"] = np.where(canceled, stay_value, 0.0)
    df["room_nights"] = np.where(canceled, 0, df["total_nights"])
    df["adr_inr"] = df["adr"] * rate
    df["segment"] = df["market_segment"].map(config.SEGMENT_LABELS).fillna(df["market_segment"])
    df["room_group"] = df["reserved_room_type"].map(config.ROOM_GROUPS).fillna("Family")
    df["room_changed"] = (df["reserved_room_type"] != df["assigned_room_type"]).astype(int)
    df["guests"] = df["adults"] + df["children"] + df["babies"]
    df["source"] = source
    return df


def load_all(rate: float) -> pd.DataFrame:
    base = preprocess(read_base(), rate, "dataset")
    added = read_added()
    if not added.empty:
        added = preprocess(added, rate, "added")
        for c in EXTRA_COLUMNS:
            if c not in base.columns:
                base[c] = np.nan
        out = pd.concat([base, added], ignore_index=True)
    else:
        out = base
    return out.sort_values("arrival_date").reset_index(drop=True)


# ----------------------------------------------------------------------------- added bookings
def append_booking(record: dict):
    row = {c: record.get(c, np.nan) for c in BASE_COLUMNS + EXTRA_COLUMNS}
    if pd.isna(row.get("booking_id")):
        row["booking_id"] = "BK-" + uuid.uuid4().hex[:8].upper()
    if pd.isna(row.get("created_at")):
        row["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    added = read_added()
    added = pd.concat([added, pd.DataFrame([row])], ignore_index=True)
    added.to_csv(config.ADDED_CSV, index=False)
    return row["booking_id"]


def write_added(df: pd.DataFrame):
    df = df[[c for c in BASE_COLUMNS + EXTRA_COLUMNS if c in df.columns]]
    df.to_csv(config.ADDED_CSV, index=False)


def validate_upload(df: pd.DataFrame):
    missing = [c for c in BASE_COLUMNS if c not in df.columns]
    return missing
