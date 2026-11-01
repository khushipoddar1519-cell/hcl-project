"""Reports – build, preview and download."""
import io
from datetime import datetime

import pandas as pd
import streamlit as st

from modules import analytics as an, components as ui, config, core


def build_sections(df: pd.DataFrame, df_hist: pd.DataFrame) -> dict[str, pd.DataFrame]:
    k = an.kpis(df)
    summary = pd.DataFrame([
        ("Total bookings", k["bookings"]), ("Cancelled bookings", k["cancelled"]),
        ("Cancellation rate (%)", round(k["cancel_rate"], 2)), ("Total revenue (₹)", round(k["revenue"])),
        ("Revenue lost to cancellations (₹)", round(k["lost_revenue"])), ("ADR (₹)", round(k["adr"])),
        ("Revenue per booking (₹)", round(k["rev_per_booking"])), ("Average lead time (days)", round(k["avg_lead"], 1)),
        ("Average stay (nights)", round(k["avg_stay"], 2)), ("Room nights sold", round(k["room_nights"])),
    ], columns=["Metric", "Value"])

    def tidy(g, col, label):
        g = g.rename(columns={col: label, "bookings": "Bookings", "cancelled": "Cancelled", "cancel_rate": "Cancel %",
                              "revenue": "Revenue (₹)", "lost_revenue": "Lost revenue (₹)", "adr": "ADR (₹)", "share": "Booking share %"})
        return g[[label, "Bookings", "Cancelled", "Cancel %", "Revenue (₹)", "Lost revenue (₹)", "ADR (₹)", "Booking share %"]].round(2)

    m = an.monthly(df)
    monthly = m.assign(Month=m["month_start"].dt.strftime("%b %Y"))[["Month", "bookings", "cancelled", "cancel_rate", "revenue", "adr"]] \
        .rename(columns={"bookings": "Bookings", "cancelled": "Cancelled", "cancel_rate": "Cancel %", "revenue": "Revenue (₹)", "adr": "ADR (₹)"}).round(2)
    secs = {
        "Executive Summary": summary,
        "Monthly Performance": monthly,
        "Market Segments": tidy(an.group_stats(df, "segment"), "segment", "Market segment"),
        "Room Categories": tidy(an.group_stats(df, "room_group"), "room_group", "Room category"),
        "Distribution Channels": tidy(an.group_stats(df, "distribution_channel"), "distribution_channel", "Channel"),
        "Top 25 Countries": tidy(an.group_stats(df, "country").sort_values("bookings", ascending=False).head(25), "country", "Country"),
        "Deposit & Customer Type": pd.concat([
            tidy(an.group_stats(df, "deposit_type"), "deposit_type", "Group").assign(Dimension="Deposit"),
            tidy(an.group_stats(df, "customer_type"), "customer_type", "Group").assign(Dimension="Customer")]),
    }
    mm = an.monthly(df_hist)
    if len(mm) >= 6:
        fc, _, _ = an.forecast_series(mm.set_index("month_start")["net_bookings"], 6)
        secs["6-Month Demand Forecast"] = fc.assign(Month=fc["month_start"].dt.strftime("%b %Y"))[["Month", "forecast", "lower", "upper"]] \
            .rename(columns={"forecast": "Forecast bookings", "lower": "Low", "upper": "High"}).round(0)
    return secs


def to_excel(secs: dict, meta: str) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, d in secs.items():
            d.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for i, c in enumerate(d.columns, 1):
                ws.column_dimensions[ws.cell(1, i).column_letter].width = max(14, len(str(c)) + 4)
        pd.DataFrame({"Report": [meta]}).to_excel(xw, sheet_name="About", index=False)
    return buf.getvalue()


def to_html(secs: dict, meta: str) -> bytes:
    css = ("body{font-family:Inter,Arial,sans-serif;background:#f3fbfa;color:#12333a;padding:30px}h1{color:#0b6f68}"
           "table{border-collapse:collapse;margin:10px 0 28px;background:#fff}th{background:#d8f2ee;text-align:left}"
           "td,th{padding:7px 12px;border-bottom:1px solid #dcebe9;font-size:14px}")
    parts = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body><h1>Hotel Analytics Report</h1><p>{meta}</p>"]
    for name, d in secs.items():
        parts.append(f"<h2>{name}</h2>" + d.to_html(index=False, border=0))
    parts.append("</body></html>")
    return "".join(parts).encode("utf-8")


def render(user):
    df_all = core.data()
    ui.page_header("Reports", "Generate, preview and download management reports for any period.")
    ctx = ui.filter_bar(df_all, "rp")
    if ui.empty_guard(ctx):
        return
    secs = build_sections(ctx["df"], ctx["base"])
    meta = f"Period {ctx['start']:%d %b %Y} – {ctx['end']:%d %b %Y} · Hotel: {ctx['hotel']} · Generated {datetime.now():%d %b %Y %H:%M} by {user['name']}"

    with ui.card("rp_pick"):
        ui.card_title("📑 Report builder", meta)
        chosen = st.multiselect("Sections to include", list(secs), default=list(secs), key="rp_sections")
        sel = {k: secs[k] for k in chosen}
        c = st.columns(4)
        if sel:
            c[0].download_button("⬇ Excel workbook", to_excel(sel, meta), "hotel_report.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="rp_xlsx")
            c[1].download_button("⬇ HTML report", to_html(sel, meta), "hotel_report.html", "text/html", key="rp_html")
            one = c[2].selectbox("CSV of", list(sel), key="rp_one", label_visibility="collapsed")
            c[3].download_button("⬇ CSV (selected)", sel[one].to_csv(index=False).encode(), f"{one.replace(' ', '_').lower()}.csv", "text/csv", key="rp_csv")
        else:
            st.info("Select at least one section.")
    for name, d in sel.items():
        with st.expander(name, expanded=(name == "Executive Summary")):
            ui.table(d)
