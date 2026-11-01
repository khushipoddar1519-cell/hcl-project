"""Pure-pandas analytics: KPIs, comparisons, grouping, forecasting and auto-insights."""
import numpy as np
import pandas as pd

from . import config


# ----------------------------------------------------------------------------- formatting
def indian(n: float, decimals: int = 0) -> str:
    """12345678 -> 1,23,45,678 (Indian digit grouping)."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "-"
    neg = n < 0
    n = abs(n)
    s = f"{n:.{decimals}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    out = whole + (("." + frac) if frac else "")
    return ("-" if neg else "") + out


def inr(n: float, decimals: int = 0) -> str:
    return "₹ " + indian(n, decimals)


def inr_short(n: float) -> str:
    """Compact rupee format: ₹ 23.40 Cr / ₹ 4.5 L."""
    n = float(n)
    a = abs(n)
    if a >= 1e7:
        return f"₹ {n / 1e7:,.2f} Cr"
    if a >= 1e5:
        return f"₹ {n / 1e5:,.2f} L"
    return inr(n)


def pct(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}%"


# ----------------------------------------------------------------------------- KPIs
def kpis(df: pd.DataFrame) -> dict:
    n = len(df)
    canc = int(df["is_canceled"].sum()) if n else 0
    revenue = float(df["revenue"].sum()) if n else 0.0
    nights = float(df["room_nights"].sum()) if n else 0.0
    lost = float(df["lost_revenue"].sum()) if n else 0.0
    return {
        "bookings": n,
        "cancelled": canc,
        "net_bookings": n - canc,
        "cancel_rate": (canc / n * 100) if n else 0.0,
        "revenue": revenue,
        "lost_revenue": lost,
        "room_nights": nights,
        "adr": (revenue / nights) if nights else 0.0,
        "rev_per_booking": (revenue / (n - canc)) if n - canc else 0.0,
        "realisation": (revenue / (revenue + lost) * 100) if (revenue + lost) else 0.0,
        "avg_lead": float(df["lead_time"].mean()) if n else 0.0,
        "avg_stay": float(df.loc[df["is_canceled"] == 0, "total_nights"].mean()) if n - canc else 0.0,
    }


def slice_window(df, start, end):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    return df[(df["arrival_date"] >= start) & (df["arrival_date"] <= end)]


def pct_change(cur, prev):
    if prev in (0, None) or (isinstance(prev, float) and np.isnan(prev)):
        return None
    return (cur - prev) / abs(prev) * 100


def compare(df_all, start, end, mode="yoy", hotel="All"):
    """KPIs for the window + % change vs last year ('yoy') or the preceding equal period ('prev')."""
    base = df_all if hotel in (None, "All") else df_all[df_all["hotel"] == hotel]
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    cur = kpis(slice_window(base, start, end))
    if mode == "yoy":
        ps, pe = start - pd.DateOffset(years=1), end - pd.DateOffset(years=1)
    else:
        length = (end - start).days + 1
        pe = start - pd.Timedelta(days=1)
        ps = pe - pd.Timedelta(days=length - 1)
    prev_df = slice_window(base, ps, pe)
    prev = kpis(prev_df)
    deltas = {k: (pct_change(cur[k], prev[k]) if len(prev_df) else None) for k in cur}
    return cur, deltas


def default_window(df_all: pd.DataFrame, months: int = 12):
    """Last `months` months of the *supplied dataset* (added bookings are ignored for the default)."""
    ref = df_all[df_all["source"] == "dataset"] if "source" in df_all.columns else df_all
    if ref.empty:
        ref = df_all
    end = ref["arrival_date"].max().normalize()
    start = max((end - pd.DateOffset(months=months) + pd.Timedelta(days=1)).normalize(),
                ref["arrival_date"].min().normalize())
    return start.date(), end.date()


# ----------------------------------------------------------------------------- grouping
def lead_bucket(s: pd.Series) -> pd.Series:
    bins = [-1, 7, 30, 90, 180, 365, 10_000]
    labels = ["0-7 days", "8-30 days", "31-90 days", "91-180 days", "181-365 days", "365+ days"]
    return pd.cut(s, bins=bins, labels=labels)


def group_stats(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[col, "bookings", "cancelled", "cancel_rate", "revenue",
                                     "lost_revenue", "adr", "share", "revenue_share"])
    g = df.groupby(col, observed=True).agg(
        bookings=("is_canceled", "size"),
        cancelled=("is_canceled", "sum"),
        revenue=("revenue", "sum"),
        lost_revenue=("lost_revenue", "sum"),
        room_nights=("room_nights", "sum"),
    ).reset_index()
    g["cancel_rate"] = g["cancelled"] / g["bookings"] * 100
    g["adr"] = np.where(g["room_nights"] > 0, g["revenue"] / g["room_nights"].replace(0, np.nan), 0)
    g["adr"] = g["adr"].fillna(0)
    g["share"] = g["bookings"] / g["bookings"].sum() * 100
    g["revenue_share"] = g["revenue"] / g["revenue"].sum() * 100 if g["revenue"].sum() else 0
    return g.sort_values("revenue", ascending=False).reset_index(drop=True)


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month_start", "bookings", "cancelled", "net_bookings", "revenue",
                                     "room_nights", "adr", "cancel_rate", "lost_revenue"])
    m = df.groupby("month_start").agg(
        bookings=("is_canceled", "size"), cancelled=("is_canceled", "sum"),
        revenue=("revenue", "sum"), room_nights=("room_nights", "sum"),
        lost_revenue=("lost_revenue", "sum")).reset_index()
    m["net_bookings"] = m["bookings"] - m["cancelled"]
    m["adr"] = np.where(m["room_nights"] > 0, m["revenue"] / m["room_nights"].replace(0, np.nan), 0)
    m["adr"] = m["adr"].fillna(0)
    m["cancel_rate"] = m["cancelled"] / m["bookings"] * 100
    return m


def top_with_others(g: pd.DataFrame, col: str, n: int = 4) -> pd.DataFrame:
    """Top-n rows by revenue + an 'Others' row (used for the dashboard table)."""
    g = g.sort_values("revenue", ascending=False)
    top, rest = g.head(n), g.iloc[n:]
    if not rest.empty:
        others = {col: "Others", "bookings": rest["bookings"].sum(), "revenue": rest["revenue"].sum()}
        top = pd.concat([top, pd.DataFrame([others])], ignore_index=True)
    total = g["revenue"].sum()
    top["share"] = top["revenue"] / total * 100 if total else 0
    return top[[col, "bookings", "revenue", "share"]]


# ----------------------------------------------------------------------------- forecasting
def forecast_series(series: pd.Series, horizon: int = 6, adj_pct: float = 0.0, z: float = 1.28):
    """Trend x seasonality forecast for a monthly series (index = month-start timestamps).

    Returns (forecast_df, seasonal_index, fitted) where forecast_df has columns
    month_start, forecast, lower, upper.
    """
    s = series.sort_index().asfreq("MS").astype(float)
    s = s.interpolate(limit_direction="both")
    n = len(s)
    if n < 4:
        val = float(s.mean()) if n else 0.0
        idx = pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1) if n else pd.Timestamp.today(),
                            periods=horizon, freq="MS")
        f = pd.DataFrame({"month_start": idx, "forecast": val, "lower": val * 0.9, "upper": val * 1.1})
        return f, pd.Series(1.0, index=range(1, 13)), s
    t = np.arange(n)
    months = s.index.month.values
    seas = pd.Series(1.0, index=range(1, 13))
    slope = intercept = 0.0
    for _ in range(4):                                   # alternate trend / seasonality estimates
        deseason = s.values / seas.reindex(months).values
        slope, intercept = np.polyfit(t, deseason, 1)
        trend = intercept + slope * t
        ratio = pd.Series(s.values / np.where(trend == 0, np.nan, trend)).groupby(months).mean()
        seas = ratio.reindex(range(1, 13)).fillna(1.0)
        seas = seas / seas.mean()
    fitted = pd.Series((intercept + slope * t) * seas.reindex(months).values, index=s.index)
    resid_sd = float(np.std(s.values - fitted.values)) if n > 2 else 0.0
    future_idx = pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    ft = np.arange(n, n + horizon)
    # damp the trend slightly so long horizons do not explode
    damp = np.array([0.5 + 0.5 * (0.85 ** i) for i in range(horizon)])
    trend_f = intercept + slope * (n - 1) + slope * (np.arange(1, horizon + 1)) * damp
    fc = trend_f * seas.reindex(future_idx.month).values * (1 + adj_pct / 100)
    recent = float(s.tail(12).mean())
    fc = np.clip(fc, recent * 0.4, recent * 2.2)
    band = z * resid_sd * np.sqrt(1 + np.arange(horizon) / 6)
    out = pd.DataFrame({"month_start": future_idx, "forecast": fc,
                        "lower": np.clip(fc - band, 0, None), "upper": fc + band})
    return out, seas, fitted


METRIC_COLS = {
    "Net bookings (non-cancelled)": "net_bookings",
    "Gross bookings": "bookings",
    "Room nights (occupancy proxy)": "room_nights",
    "Revenue": "revenue",
    "ADR": "adr",
    "Cancellations": "cancelled",
}


# ----------------------------------------------------------------------------- insights
def _span(months):
    months = sorted(set(months))
    if not months:
        return ""
    runs, cur = [], [months[0]]
    for m in months[1:]:
        if m == cur[-1] + 1:
            cur.append(m)
        else:
            runs.append(cur)
            cur = [m]
    runs.append(cur)
    return ", ".join(config.MONTH_ABBR[r[0] - 1] if len(r) == 1
                     else f"{config.MONTH_ABBR[r[0] - 1]}–{config.MONTH_ABBR[r[-1] - 1]}" for r in runs)


def insights(df_win: pd.DataFrame, df_hist: pd.DataFrame) -> list[dict]:
    """Auto-generated insight cards. First three are the headline cards shown on Home."""
    out = []
    if df_win.empty:
        return out
    # 1. highest cancellation
    rooms = group_stats(df_win, "room_group")
    rooms = rooms[rooms["bookings"] >= 200]
    segs = group_stats(df_win, "segment")
    segs = segs[segs["bookings"] >= 500]
    if not rooms.empty and not segs.empty:
        r = rooms.sort_values("cancel_rate", ascending=False).iloc[0]
        s = segs.sort_values("cancel_rate", ascending=False).iloc[0]
        out.append(dict(kind="cancel", title="Highest Cancellation Rate",
                        desc=f"{r['room_group']} Room ({r['cancel_rate']:.2f}%) – Market Segment: {s['segment']} ({s['cancel_rate']:.1f}%)",
                        page="cancel"))
    # 2. demand forecast
    m = monthly(df_hist)
    if len(m) >= 6:
        fc, _, _ = forecast_series(m.set_index("month_start")["net_bookings"], 6)
        last6 = m.sort_values("month_start").tail(6)["net_bookings"].sum()
        chg = pct_change(fc["forecast"].sum(), last6)
        if chg is not None:
            word = "increase" if chg >= 0 else "decrease"
            out.append(dict(kind="demand", title="Demand Forecast",
                            desc=f"Demand expected to {word} by {abs(chg):.0f}% in next 6 months.", page="forecast"))
    # 3. revenue opportunity
    if len(m) >= 12:
        _, seas, _ = forecast_series(m.set_index("month_start")["revenue"], 1)
        top = seas.sort_values(ascending=False).head(3)
        lift = (top.mean() - 1) * 100
        out.append(dict(kind="revenue", title="Revenue Opportunity",
                        desc=f"Peak season ({_span(list(top.index))}) shows {lift:.0f}% higher revenue potential.",
                        page="revenue"))
    # extras for 'View all'
    d = df_win
    dep = group_stats(d, "deposit_type")
    dep = dep[dep["bookings"] >= 200]
    if not dep.empty:
        r = dep.sort_values("cancel_rate", ascending=False).iloc[0]
        out.append(dict(kind="cancel", title="Deposit Policy",
                        desc=f"'{r['deposit_type']}' bookings cancel at {r['cancel_rate']:.1f}% – review the deposit policy.",
                        page="cancel"))
    long_ = d[d["lead_time"] > 180]
    short_ = d[d["lead_time"] <= 30]
    if len(long_) > 100 and len(short_) > 100:
        out.append(dict(kind="cancel", title="Lead Time Risk",
                        desc=f"Bookings made 180+ days ahead cancel {long_['is_canceled'].mean() * 100:.1f}% vs "
                             f"{short_['is_canceled'].mean() * 100:.1f}% for ≤30 days.", page="cancel"))
    with_req = d[d["total_of_special_requests"] > 0]
    no_req = d[d["total_of_special_requests"] == 0]
    if len(with_req) > 100 and len(no_req) > 100:
        out.append(dict(kind="demand", title="Special Requests",
                        desc=f"Guests with special requests cancel {with_req['is_canceled'].mean() * 100:.1f}% vs "
                             f"{no_req['is_canceled'].mean() * 100:.1f}% without – personalise to retain guests.", page="segments"))
    rep = d[d["is_repeated_guest"] == 1]
    new = d[d["is_repeated_guest"] == 0]
    if len(rep) > 100 and len(new) > 100:
        out.append(dict(kind="revenue", title="Loyal Guests",
                        desc=f"Repeat guests cancel only {rep['is_canceled'].mean() * 100:.1f}% (new guests {new['is_canceled'].mean() * 100:.1f}%).",
                        page="segments"))
    return out


def tip(df_win: pd.DataFrame, reduction: float = 0.20):
    """Best segment to focus on and the revenue uplift if its cancellations fall by `reduction`."""
    if df_win.empty:
        return None
    g = group_stats(df_win, "segment")
    if g.empty or g["revenue"].sum() == 0:
        return None
    r = g.sort_values("lost_revenue", ascending=False).iloc[0]
    uplift = r["lost_revenue"] * reduction / g["revenue"].sum() * 100
    return {"segment": r["segment"], "uplift": float(uplift), "reduction": reduction}
