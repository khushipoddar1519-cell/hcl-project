"""Business logic and analytics bridge for the Hotel Analytics backend."""
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
import io
import pandas as pd
import numpy as np

from modules import config, data_loader, analytics as an, model, auth, settings
from backend.schemas import BookingInput, PredictionResponse, RiskDriver

class AnalyticsService:
    def __init__(self):
        self._df = None
        self._bundle = None
        self._last_loaded = None

    def get_settings(self) -> dict:
        return settings.load()

    def update_settings(self, new_cfg: dict) -> dict:
        curr = settings.load()
        curr.update(new_cfg)
        settings.save(curr)
        # Invalidate loaded df so exchange rate updates
        self._df = None
        return curr

    def get_df(self, force_reload: bool = False) -> pd.DataFrame:
        if self._df is None or force_reload:
            cfg = self.get_settings()
            rate = float(cfg.get("eur_to_inr", 90.0))
            self._df = data_loader.load_all(rate)
            self._last_loaded = datetime.now()
        return self._df

    def get_model_bundle(self, force_retrain: bool = False):
        if self._bundle is None or force_retrain:
            if not force_retrain:
                self._bundle = model.load_bundle()
            if self._bundle is None or force_retrain:
                df = self.get_df()
                self._bundle = model.train(df)
        return self._bundle

    def filter_df(self, df: pd.DataFrame, start_date: Optional[str] = None,
                  end_date: Optional[str] = None, hotel: Optional[str] = None) -> pd.DataFrame:
        d = df.copy()
        if hotel and hotel not in ("All", "all", "ALL"):
            d = d[d["hotel"] == hotel]
        if start_date:
            try:
                start_ts = pd.Timestamp(start_date)
                d = d[d["arrival_date"] >= start_ts]
            except Exception:
                pass
        if end_date:
            try:
                end_ts = pd.Timestamp(end_date)
                d = d[d["arrival_date"] <= end_ts]
            except Exception:
                pass
        return d

    def get_kpis(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                 hotel: Optional[str] = None) -> dict:
        df_all = self.get_df()
        cfg = self.get_settings()
        
        # Determine effective dates
        if not start_date or not end_date:
            def_start, def_end = an.default_window(df_all, int(cfg.get("window_months", 12)))
            start_date = str(def_start) if not start_date else start_date
            end_date = str(def_end) if not end_date else end_date

        cur, deltas = an.compare(df_all, start_date, end_date, mode="prev", hotel=hotel or "All")
        
        # Add human-friendly formatted values
        cur["revenue_formatted"] = an.inr_short(cur["revenue"])
        cur["lost_revenue_formatted"] = an.inr_short(cur["lost_revenue"])
        cur["adr_formatted"] = an.inr(cur["adr"])
        cur["cancel_rate_pct"] = round(cur["cancel_rate"], 1)
        cur["bookings_formatted"] = an.indian(cur["bookings"])
        cur["start_date"] = start_date
        cur["end_date"] = end_date
        
        # Generate auto-insights for this window
        window_df = self.filter_df(df_all, start_date, end_date, hotel)
        insights_list = an.insights(window_df, df_all)
        tip_data = an.tip(window_df)

        return {
            "current": cur,
            "deltas": {k: (round(v, 1) if v is not None else None) for k, v in deltas.items()},
            "insights": insights_list,
            "tip": tip_data
        }

    def get_trend(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                  hotel: Optional[str] = None) -> List[dict]:
        df_all = self.get_df()
        df = self.filter_df(df_all, start_date, end_date, hotel)
        m = an.monthly(df)
        if m.empty:
            return []
        m = m.sort_values("month_start")
        result = []
        for _, row in m.iterrows():
            result.append({
                "month": row["month_start"].strftime("%b %Y"),
                "date": row["month_start"].strftime("%Y-%m-%d"),
                "bookings": int(row["bookings"]),
                "cancelled": int(row["cancelled"]),
                "net_bookings": int(row["net_bookings"]),
                "revenue": float(row["revenue"]),
                "adr": float(row["adr"]),
                "cancel_rate": round(float(row["cancel_rate"]), 1)
            })
        return result

    def get_segments(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                     hotel: Optional[str] = None) -> List[dict]:
        df = self.filter_df(self.get_df(), start_date, end_date, hotel)
        g = an.group_stats(df, "segment")
        if g.empty:
            return []
        records = []
        for _, row in g.iterrows():
            records.append({
                "segment": str(row["segment"]),
                "bookings": int(row["bookings"]),
                "cancelled": int(row["cancelled"]),
                "cancel_rate": round(float(row["cancel_rate"]), 1),
                "revenue": float(row["revenue"]),
                "revenue_formatted": an.inr_short(row["revenue"]),
                "adr": round(float(row["adr"]), 1),
                "share": round(float(row["share"]), 1),
                "revenue_share": round(float(row["revenue_share"]), 1)
            })
        return records

    def get_rooms(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                  hotel: Optional[str] = None) -> List[dict]:
        df = self.filter_df(self.get_df(), start_date, end_date, hotel)
        g = an.group_stats(df, "room_group")
        if g.empty:
            return []
        records = []
        for _, row in g.iterrows():
            rg = str(row["room_group"])
            records.append({
                "room_group": rg,
                "color": config.ROOM_COLORS.get(rg, "#7c6cf0"),
                "bookings": int(row["bookings"]),
                "cancelled": int(row["cancelled"]),
                "cancel_rate": round(float(row["cancel_rate"]), 1),
                "revenue": float(row["revenue"]),
                "revenue_formatted": an.inr_short(row["revenue"]),
                "adr": round(float(row["adr"]), 1),
                "share": round(float(row["share"]), 1),
                "revenue_share": round(float(row["revenue_share"]), 1)
            })
        return records

    def get_channels(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                     hotel: Optional[str] = None) -> List[dict]:
        df = self.filter_df(self.get_df(), start_date, end_date, hotel)
        g = an.group_stats(df, "distribution_channel")
        return [
            {
                "channel": str(r["distribution_channel"]),
                "bookings": int(r["bookings"]),
                "cancel_rate": round(float(r["cancel_rate"]), 1),
                "revenue": float(r["revenue"]),
                "share": round(float(r["share"]), 1)
            }
            for _, r in g.iterrows()
        ]

    def get_cancellation_drivers(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                                 hotel: Optional[str] = None) -> dict:
        df = self.filter_df(self.get_df(), start_date, end_date, hotel)
        if df.empty:
            return {}

        # Lead time buckets
        df_copy = df.copy()
        df_copy["lead_bucket"] = an.lead_bucket(df_copy["lead_time"])
        lead_stats = an.group_stats(df_copy, "lead_bucket")
        lead_list = [
            {
                "bucket": str(r["lead_bucket"]),
                "bookings": int(r["bookings"]),
                "cancel_rate": round(float(r["cancel_rate"]), 1)
            }
            for _, r in lead_stats.iterrows()
        ]

        # Deposit types
        dep_stats = an.group_stats(df, "deposit_type")
        dep_list = [
            {
                "deposit_type": str(r["deposit_type"]),
                "bookings": int(r["bookings"]),
                "cancel_rate": round(float(r["cancel_rate"]), 1)
            }
            for _, r in dep_stats.iterrows()
        ]

        # Special requests
        df_copy["req_bucket"] = df_copy["total_of_special_requests"].apply(
            lambda x: "0 Requests" if x == 0 else ("1 Request" if x == 1 else "2+ Requests")
        )
        req_stats = an.group_stats(df_copy, "req_bucket")
        req_list = [
            {
                "requests": str(r["req_bucket"]),
                "bookings": int(r["bookings"]),
                "cancel_rate": round(float(r["cancel_rate"]), 1)
            }
            for _, r in req_stats.iterrows()
        ]

        # Customer types
        cust_stats = an.group_stats(df, "customer_type")
        cust_list = [
            {
                "customer_type": str(r["customer_type"]),
                "bookings": int(r["bookings"]),
                "cancel_rate": round(float(r["cancel_rate"]), 1)
            }
            for _, r in cust_stats.iterrows()
        ]

        return {
            "lead_time": lead_list,
            "deposit_types": dep_list,
            "special_requests": req_list,
            "customer_types": cust_list
        }

    def get_geography(self, limit: int = 15) -> List[dict]:
        df = self.get_df()
        g = an.group_stats(df, "country").head(limit)
        records = []
        for _, r in g.iterrows():
            code = str(r["country"])
            records.append({
                "country_code": code,
                "country_name": config.COUNTRY_NAMES.get(code, code),
                "bookings": int(r["bookings"]),
                "cancel_rate": round(float(r["cancel_rate"]), 1),
                "revenue": float(r["revenue"]),
                "revenue_formatted": an.inr_short(r["revenue"])
            })
        return records

    def get_forecast(self, metric: str = "net_bookings", horizon: int = 6,
                     scenario_pct: float = 0.0, hotel: Optional[str] = None) -> dict:
        df_all = self.get_df()
        if hotel and hotel != "All":
            df_all = df_all[df_all["hotel"] == hotel]
        m = an.monthly(df_all)
        if len(m) < 4:
            return {"metric": metric, "horizon": horizon, "data": [], "seasonal_index": {}}

        m_idx = m.set_index("month_start")
        col = metric if metric in m_idx.columns else "net_bookings"
        series = m_idx[col]
        fc_df, seas, fitted = an.forecast_series(series, horizon=horizon, adj_pct=scenario_pct)

        # Build combined historical tail + forecast points
        tail = m.tail(6)
        hist_points = [
            {
                "month": r["month_start"].strftime("%b %Y"),
                "date": r["month_start"].strftime("%Y-%m-%d"),
                "actual": float(r[col]),
                "forecast": None,
                "lower": None,
                "upper": None,
                "is_future": False
            }
            for _, r in tail.iterrows()
        ]

        future_points = [
            {
                "month": r["month_start"].strftime("%b %Y"),
                "date": r["month_start"].strftime("%Y-%m-%d"),
                "actual": None,
                "forecast": round(float(r["forecast"]), 1),
                "lower": round(float(r["lower"]), 1),
                "upper": round(float(r["upper"]), 1),
                "is_future": True
            }
            for _, r in fc_df.iterrows()
        ]

        seas_dict = {config.MONTH_ABBR[m - 1]: round(float(seas.get(m, 1.0)), 2) for m in range(1, 13)}

        return {
            "metric": metric,
            "horizon": horizon,
            "scenario_pct": scenario_pct,
            "points": hist_points + future_points,
            "seasonal_index": seas_dict
        }

    def predict_risk(self, booking: BookingInput) -> PredictionResponse:
        bundle = self.get_model_bundle()
        cfg = self.get_settings()
        rate = float(cfg.get("eur_to_inr", 90.0))

        # Convert booking to model feature row
        b_dict = booking.model_dump()
        raw_adr = float(b_dict.get("adr", 120.0))
        if raw_adr > 500:
            b_dict["adr"] = raw_adr / rate
            adr_inr = raw_adr
        else:
            adr_inr = raw_adr * rate

        # Default assigned room type to reserved if not provided
        b_dict.setdefault("assigned_room_type", b_dict.get("reserved_room_type", "A"))

        prob = model.predict_proba(bundle, b_dict)
        prob_pct = round(prob * 100, 1)

        low_max = float(cfg.get("low_risk_max", 30.0))
        high_min = float(cfg.get("high_risk_min", 60.0))
        level = model.risk_level(prob_pct, low_max, high_min)

        # Revenue at risk: ADR * nights * probability
        total_nights = max(1, b_dict.get("stays_in_weekend_nights", 0) + b_dict.get("stays_in_week_nights", 0))
        stay_val = adr_inr * total_nights
        revenue_at_risk = round(stay_val * prob, 0)

        # Factor explanations
        exp_df = model.explain(bundle, b_dict, top_n=6)
        drivers = [
            RiskDriver(feature=row["feature"], impact=round(float(row["impact"]), 1))
            for _, row in exp_df.iterrows()
        ]

        # Actionable recommendations
        recs = self._get_recommendations(b_dict, prob_pct, level)

        return PredictionResponse(
            probability=round(prob, 4),
            probability_pct=prob_pct,
            risk_level=level,
            revenue_at_risk=revenue_at_risk,
            currency_symbol="₹",
            drivers=drivers,
            recommendations=recs
        )

    def _get_recommendations(self, row: dict, p: float, level: str) -> List[str]:
        r = []
        if level == "High":
            r.append("Request a 30-50% prepayment or credit card guarantee before confirming the booking.")
            r.append(f"High risk ({p:.0f}% chance of cancellation): plan a 1-room overbooking buffer.")
            r.append("Send proactive check-in confirmation reminders at 30, 14, and 3 days before arrival.")
        elif level == "Medium":
            r.append("Send a personalised confirmation e-mail with room upgrade options 7 days prior.")
            r.append("Offer a flexible complimentary add-on (e.g. early check-in or breakfast) to solidify reservation.")
        else:
            r.append("Standard confirmation sufficient – this reservation has a very high retention probability.")

        if row.get("lead_time", 0) > 120:
            r.append(f"Extended lead time ({row['lead_time']} days): schedule a midway engagement touchpoint at 60 days.")
        if row.get("total_of_special_requests", 0) == 0 and level != "Low":
            r.append("Guest has zero special requests: prompt guest with a welcome questionnaire to build attachment.")
        if row.get("market_segment") == "Online TA" and level != "Low":
            r.append("Online Travel Agency booking: offer direct booking perks for future stays to reduce commission and churn.")
        if row.get("deposit_type") == "No Deposit" and level == "High":
            r.append("Switch this rate plan to a partially refundable or advance purchase structure.")
        if row.get("is_repeated_guest"):
            r.append("Valued repeat guest: recognize loyalty upon arrival with VIP welcome amenities.")
        return r

    def add_booking(self, booking: BookingInput, user_name: str = "Admin") -> dict:
        b_dict = booking.model_dump()
        bundle = self.get_model_bundle()
        cfg = self.get_settings()
        rate = float(cfg.get("eur_to_inr", 90.0))

        raw_adr = float(b_dict.get("adr", 120.0))
        if raw_adr > 500:
            b_dict["adr"] = raw_adr / rate

        prob = model.predict_proba(bundle, b_dict)
        prob_pct = round(prob * 100, 1)
        low_max = float(cfg.get("low_risk_max", 30.0))
        high_min = float(cfg.get("high_risk_min", 60.0))
        level = model.risk_level(prob_pct, low_max, high_min)

        # Fill model and data fields
        now = datetime.now()
        b_dict["risk_score"] = prob_pct
        b_dict["risk_level"] = level
        b_dict["created_by"] = user_name
        b_dict["created_at"] = now.strftime("%Y-%m-%d %H:%M")
        b_dict["reservation_status"] = "Confirmed"
        b_dict["reservation_status_date"] = now.strftime("%Y-%m-%d")
        b_dict["is_canceled"] = 0

        # Arrival date handling
        if not b_dict.get("arrival_date_year"):
            b_dict["arrival_date_year"] = now.year
        if not b_dict.get("arrival_date_week_number"):
            b_dict["arrival_date_week_number"] = now.isocalendar()[1]

        booking_id = data_loader.append_booking(b_dict)
        # Reload dataset
        self.get_df(force_reload=True)

        return {
            "booking_id": booking_id,
            "risk_score": prob_pct,
            "risk_level": level,
            "message": "Booking successfully registered and added to database."
        }

    def list_bookings(self, limit: int = 50, offset: int = 0, search: Optional[str] = None,
                      hotel: Optional[str] = None, status: Optional[str] = None,
                      risk_level: Optional[str] = None) -> dict:
        df = self.get_df()
        d = df.copy()

        if hotel and hotel != "All":
            d = d[d["hotel"] == hotel]
        if status and status != "All":
            d = d[d["reservation_status"] == status]
        if risk_level and risk_level != "All" and "risk_level" in d.columns:
            d = d[d["risk_level"] == risk_level]
        if search:
            s = search.lower().strip()
            mask = pd.Series(False, index=d.index)
            if "booking_id" in d.columns:
                mask |= d["booking_id"].astype(str).str.lower().str.contains(s, na=False)
            if "guest_name" in d.columns:
                mask |= d["guest_name"].astype(str).str.lower().str.contains(s, na=False)
            if "country" in d.columns:
                mask |= d["country"].astype(str).str.lower().str.contains(s, na=False)
            d = d[mask]

        total = len(d)
        page_df = d.iloc[offset: offset + limit]

        items = []
        for _, r in page_df.iterrows():
            bid = r["booking_id"] if pd.notna(r.get("booking_id")) else f"LEGACY-{r.name}"
            gname = r["guest_name"] if pd.notna(r.get("guest_name")) else f"Guest #{r.name + 1}"
            r_score = round(float(r["risk_score"]), 1) if pd.notna(r.get("risk_score")) else None
            r_level = str(r["risk_level"]) if pd.notna(r.get("risk_level")) else ("Canceled" if r["is_canceled"] == 1 else "Normal")
            
            items.append({
                "booking_id": bid,
                "guest_name": gname,
                "hotel": str(r["hotel"]),
                "arrival_date": r["arrival_date"].strftime("%Y-%m-%d"),
                "total_nights": int(r["total_nights"]),
                "adults": int(r["adults"]),
                "children": int(r["children"]),
                "room_group": str(r["room_group"]),
                "market_segment": str(r["segment"]),
                "deposit_type": str(r["deposit_type"]),
                "adr": round(float(r["adr_inr"]), 0),
                "revenue": round(float(r["revenue"]), 0),
                "revenue_formatted": an.inr_short(r["revenue"]),
                "reservation_status": str(r["reservation_status"]),
                "is_canceled": int(r["is_canceled"]),
                "risk_score": r_score,
                "risk_level": r_level,
                "created_at": str(r.get("created_at", ""))
            })

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "bookings": items
        }

    def update_booking_status(self, booking_id: str, new_status: str) -> bool:
        added = data_loader.read_added()
        if added.empty or "booking_id" not in added.columns:
            return False
        mask = added["booking_id"] == booking_id
        if not mask.any():
            return False
        
        added.loc[mask, "reservation_status"] = new_status
        if new_status in ("Canceled", "No-Show"):
            added.loc[mask, "is_canceled"] = 1
        elif new_status == "Check-Out":
            added.loc[mask, "is_canceled"] = 0
            
        data_loader.write_added(added)
        self.get_df(force_reload=True)
        return True

    def get_model_diagnostics(self) -> dict:
        bundle = self.get_model_bundle()
        m = bundle.get("metrics", {})
        imp_df = bundle.get("importance", pd.DataFrame())
        
        features_list = []
        if not imp_df.empty:
            for _, r in imp_df.head(10).iterrows():
                feat = str(r["feature"])
                features_list.append({
                    "feature": model.FRIENDLY.get(feat, feat),
                    "importance": round(float(r["importance"]), 4)
                })

        return {
            "accuracy": round(float(m.get("accuracy", 0.869)), 3),
            "auc": round(float(m.get("auc", 0.944)), 3),
            "precision": round(float(m.get("precision", 0.84)), 3),
            "recall": round(float(m.get("recall", 0.82)), 3),
            "f1": round(float(m.get("f1", 0.83)), 3),
            "n_training_rows": bundle.get("n_rows", 119390),
            "trained_at": bundle.get("trained_at", "Pre-trained"),
            "confusion_matrix": m.get("confusion", [[0, 0], [0, 0]]),
            "top_features": features_list
        }

    def export_data(self, dataset_type: str = "kpis") -> bytes:
        df = self.get_df()
        out = io.StringIO()
        if dataset_type == "bookings":
            export_cols = ["hotel", "arrival_date", "lead_time", "stays_in_weekend_nights",
                           "stays_in_week_nights", "adults", "children", "market_segment",
                           "deposit_type", "adr", "is_canceled", "reservation_status"]
            if "booking_id" in df.columns:
                export_cols.insert(0, "booking_id")
            df[export_cols].head(5000).to_csv(out, index=False)
        elif dataset_type == "monthly":
            m = an.monthly(df)
            m.to_csv(out, index=False)
        else: # default segments & overview
            g = an.group_stats(df, "segment")
            g.to_csv(out, index=False)
        return out.getvalue().encode("utf-8")

service = AnalyticsService()

