"""Cancellation-risk model (HistGradientBoosting) – training, persistence and explanations."""
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from . import config

CAT = ["hotel", "arrival_date_month", "meal", "country_grp", "market_segment", "distribution_channel",
       "reserved_room_type", "deposit_type", "customer_type"]
NUM = ["lead_time", "stays_in_weekend_nights", "stays_in_week_nights", "adults", "children", "babies",
       "is_repeated_guest", "previous_cancellations", "previous_bookings_not_canceled", "booking_changes",
       "days_in_waiting_list", "adr", "required_car_parking_spaces", "total_of_special_requests"]
FEATURES = CAT + NUM

FRIENDLY = {
    "lead_time": "Lead time", "deposit_type": "Deposit type", "market_segment": "Market segment",
    "previous_cancellations": "Previous cancellations", "total_of_special_requests": "Special requests",
    "booking_changes": "Booking changes", "customer_type": "Customer type",
    "is_repeated_guest": "Repeat guest", "adr": "Room rate (ADR)", "days_in_waiting_list": "Waiting list days",
    "required_car_parking_spaces": "Parking requested", "distribution_channel": "Distribution channel",
    "country_grp": "Guest country", "hotel": "Hotel", "arrival_date_month": "Arrival month",
    "meal": "Meal plan", "reserved_room_type": "Room type", "adults": "Adults", "children": "Children",
    "babies": "Babies", "stays_in_weekend_nights": "Weekend nights", "stays_in_week_nights": "Week nights",
    "previous_bookings_not_canceled": "Previous completed stays",
}
EXPLAIN_FEATURES = ["lead_time", "deposit_type", "market_segment", "previous_cancellations",
                    "total_of_special_requests", "booking_changes", "customer_type", "is_repeated_guest",
                    "adr", "days_in_waiting_list", "required_car_parking_spaces", "distribution_channel"]


def _features(df: pd.DataFrame, top_countries) -> pd.DataFrame:
    X = df.copy()
    X["country_grp"] = np.where(X["country"].isin(top_countries), X["country"], "Other")
    X["children"] = X["children"].fillna(0)
    return X[FEATURES]


def _pipeline() -> Pipeline:
    pre = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                                encoded_missing_value=-1), CAT)],
        remainder="passthrough")
    clf = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.08, max_leaf_nodes=48, l2_regularization=1.0,
        categorical_features=list(range(len(CAT))), random_state=42)
    return Pipeline([("pre", pre), ("clf", clf)])


def train(df: pd.DataFrame, progress=None) -> dict:
    """Train on completed reservations (excludes bookings that are still 'Confirmed')."""
    d = df[df["reservation_status"].isin(["Check-Out", "Canceled", "No-Show"])].copy()
    top_countries = d["country"].value_counts().head(25).index.tolist()
    X, y = _features(d, top_countries), d["is_canceled"].astype(int)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipe = _pipeline().fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "accuracy": accuracy_score(yte, pred), "precision": precision_score(yte, pred),
        "recall": recall_score(yte, pred), "f1": f1_score(yte, pred), "auc": roc_auc_score(yte, proba),
        "confusion": confusion_matrix(yte, pred).tolist(), "test_rows": int(len(yte)),
        "base_rate": float(y.mean()),
    }
    # permutation importance on a sample of the hold-out set
    samp = Xte.sample(min(5000, len(Xte)), random_state=1)
    imp = permutation_importance(pipe, samp, yte.loc[samp.index], scoring="roc_auc", n_repeats=3,
                                 random_state=1, n_jobs=1)
    importance = (pd.DataFrame({"feature": FEATURES, "importance": imp.importances_mean})
                  .sort_values("importance", ascending=False).reset_index(drop=True))
    defaults = {c: X[c].mode().iloc[0] for c in CAT}
    defaults.update({c: float(X[c].median()) for c in NUM})
    defaults["total_of_special_requests"] = 1.0
    defaults["booking_changes"] = 0.0
    defaults["previous_cancellations"] = 0.0
    defaults["is_repeated_guest"] = 0.0
    defaults["days_in_waiting_list"] = 0.0
    defaults["required_car_parking_spaces"] = 0.0
    bundle = {"pipeline": pipe, "top_countries": top_countries, "metrics": metrics,
              "importance": importance, "defaults": defaults, "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "n_rows": int(len(d))}
    joblib.dump(bundle, config.MODEL_FILE)
    return bundle


def load_bundle():
    if config.MODEL_FILE.exists():
        try:
            return joblib.load(config.MODEL_FILE)
        except Exception:
            return None
    return None


def _row_df(row: dict, bundle) -> pd.DataFrame:
    r = dict(row)
    r.setdefault("country", "Other")
    df = pd.DataFrame([r])
    return _features(df, bundle["top_countries"])


def predict_proba(bundle, row: dict) -> float:
    return float(bundle["pipeline"].predict_proba(_row_df(row, bundle))[0, 1])


def explain(bundle, row: dict, top_n: int = 6) -> pd.DataFrame:
    """What-if explanation: change in risk if each factor were set to a 'typical' value."""
    base = predict_proba(bundle, row)
    X = _row_df(row, bundle)
    rows = []
    for f in EXPLAIN_FEATURES:
        alt = X.copy()
        alt[f] = bundle["defaults"][f]
        if f in CAT:
            alt[f] = bundle["defaults"][f]
        p_alt = float(bundle["pipeline"].predict_proba(alt)[0, 1])
        rows.append({"feature": FRIENDLY.get(f, f), "impact": (base - p_alt) * 100})
    out = pd.DataFrame(rows)
    out = out.reindex(out["impact"].abs().sort_values(ascending=False).index)
    strong = out[out["impact"].abs() >= 0.1]
    out = (strong if len(strong) >= 3 else out).head(top_n)
    return out.sort_values("impact").reset_index(drop=True)


def risk_level(p_pct: float, low_max: float, high_min: float) -> str:
    return "Low" if p_pct < low_max else ("High" if p_pct >= high_min else "Medium")
