"""Add Booking & Cancellation-Risk calculator."""
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import analytics as an, components as ui, config, core, data_loader, model, settings

MEALS = {"BB": "BB – Bed & Breakfast", "HB": "HB – Half board", "FB": "FB – Full board", "SC": "SC – Self catering", "Undefined": "Undefined"}
CHANNELS = ["Direct", "Corporate", "TA/TO", "GDS", "Undefined"]
DEPOSITS = ["No Deposit", "Non Refund", "Refundable"]
CUSTOMERS = ["Transient", "Transient-Party", "Contract", "Group"]


def _nights(arrival, departure):
    wk = we = 0
    d = arrival
    while d < departure:
        if d.weekday() >= 5:
            we += 1
        else:
            wk += 1
        d += timedelta(days=1)
    return we, wk


def _recommendations(row, p, level, value_inr):
    r = []
    if level == "High":
        r.append("Request a prepayment or card guarantee before confirming the booking.")
        r.append("Send reconfirmation messages 30 and 7 days before arrival.")
        r.append(f"Plan overbooking buffer – expected cancellation probability is {p:.0f}%.")
    elif level == "Medium":
        r.append("Send a reconfirmation e-mail 7 days before arrival.")
        r.append("Offer a flexible add-on (breakfast, late checkout) to strengthen commitment.")
    else:
        r.append("Standard confirmation is sufficient – this booking is likely to stay.")
    if row["lead_time"] > 120:
        r.append("Long lead time: add a mid-way check-in with the guest (e.g. at 60 days).")
    if row["total_of_special_requests"] == 0 and level != "Low":
        r.append("Invite the guest to share special requests – engaged guests cancel far less.")
    if row["market_segment"] == "Online TA" and level != "Low":
        r.append("Offer a direct-booking incentive to move this guest off the OTA channel.")
    if row["deposit_type"] == "No Deposit" and level == "High":
        r.append("Switch the rate plan to a partially refundable / deposit rate.")
    if row["is_repeated_guest"]:
        r.append("Repeat guest – consider a loyalty perk to lock in the stay.")
    return r


def render(user):
    df_all = core.data()
    cfg = settings.load()
    rate = float(cfg["eur_to_inr"])
    ui.page_header("Add Booking & Cancellation Risk",
                   "Enter a reservation, get its cancellation probability instantly, then save it to the booking database.")
    bundle = core.get_model()
    ds = df_all[df_all["source"] == "dataset"]
    base_max = ds["arrival_date"].max().date()
    countries = df_all["country"].value_counts().head(40).index.tolist()
    segs = [s for s in config.SEGMENT_LABELS.values() if s != "Undefined"]
    rooms = list(config.ROOM_GROUPS)

    left, right = st.columns([5.2, 4.3])
    with left:
        with ui.card("bk_form"):
            ui.card_title("📝 Reservation details", f"Dataset ends {base_max:%d %b %Y} – the date pickers start just after it so the booking shows in the dashboards.")
            with st.form("booking_form"):
                c1, c2 = st.columns(2)
                guest = c1.text_input("Guest name", placeholder="e.g. Aarav Mehta")
                hotel = c2.selectbox("Hotel", ["City Hotel", "Resort Hotel"])
                c1, c2, c3 = st.columns(3)
                booking_date = c1.date_input("Booking date", value=base_max - timedelta(days=30))
                arrival = c2.date_input("Check-in", value=base_max + timedelta(days=14))
                departure = c3.date_input("Check-out", value=base_max + timedelta(days=17))
                c1, c2, c3 = st.columns(3)
                adults = c1.number_input("Adults", 0, 10, 2)
                children = c2.number_input("Children", 0, 10, 0)
                babies = c3.number_input("Babies", 0, 5, 0)
                c1, c2, c3 = st.columns(3)
                segment = c1.selectbox("Market segment", segs, index=segs.index("Online Travel Agency"))
                channel = c2.selectbox("Distribution channel", CHANNELS, index=2)
                customer = c3.selectbox("Customer type", CUSTOMERS)
                c1, c2, c3 = st.columns(3)
                room = c1.selectbox("Room type", rooms, format_func=lambda r: f"{r} – {config.ROOM_GROUPS[r]}")
                meal = c2.selectbox("Meal plan", list(MEALS), format_func=lambda m: MEALS[m])
                deposit = c3.selectbox("Deposit type", DEPOSITS)
                c1, c2 = st.columns(2)
                country = c1.selectbox("Guest country", countries, format_func=lambda c: f"{c} – {config.COUNTRY_NAMES.get(c, '')}".strip(" –"))
                adr_inr = c2.number_input("Room rate / ADR (₹ per night)", 500.0, 100000.0, 5420.0, step=100.0)
                with st.expander("Guest history & extras", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    repeated = c1.checkbox("Repeat guest")
                    prev_c = c2.number_input("Previous cancellations", 0, 30, 0)
                    prev_nc = c3.number_input("Previous completed stays", 0, 60, 0)
                    c1, c2, c3, c4 = st.columns(4)
                    changes = c1.number_input("Booking changes", 0, 20, 0)
                    wait = c2.number_input("Days on waiting list", 0, 400, 0)
                    park = c3.number_input("Parking spaces", 0, 5, 0)
                    reqs = c4.number_input("Special requests", 0, 5, 0)
                go_btn = ui.stretch(st.form_submit_button, "Calculate Cancellation Risk", type="primary")

        if go_btn:
            if departure <= arrival:
                st.error("Check-out must be after check-in.")
            elif arrival < booking_date:
                st.error("Check-in cannot be before the booking date.")
            elif adults + children + babies == 0:
                st.error("At least one guest is required.")
            else:
                we, wk = _nights(arrival, departure)
                row = dict(hotel=hotel, arrival_date_month=config.MONTHS[arrival.month - 1], meal=meal, country=country,
                           market_segment=config.SEGMENT_REVERSE.get(segment, segment), distribution_channel=channel,
                           reserved_room_type=room, deposit_type=deposit, customer_type=customer,
                           lead_time=(arrival - booking_date).days, stays_in_weekend_nights=we, stays_in_week_nights=wk,
                           adults=adults, children=children, babies=babies, is_repeated_guest=int(repeated),
                           previous_cancellations=prev_c, previous_bookings_not_canceled=prev_nc, booking_changes=changes,
                           days_in_waiting_list=wait, adr=adr_inr / rate, required_car_parking_spaces=park,
                           total_of_special_requests=reqs)
                p = model.predict_proba(bundle, row) * 100
                level = model.risk_level(p, cfg["low_risk_max"], cfg["high_risk_min"])
                record = dict(row, is_canceled=0, arrival_date_year=arrival.year,
                              arrival_date_week_number=arrival.isocalendar()[1], arrival_date_day_of_month=arrival.day,
                              assigned_room_type=room, agent=None, company=None, reservation_status="Confirmed",
                              reservation_status_date=str(booking_date), guest_name=guest or "Walk-in guest",
                              risk_score=round(p, 1), risk_level=level, created_by=user["username"])
                st.session_state["last_risk"] = dict(row=row, record=record, p=p, level=level, nights=we + wk,
                                                     expl=model.explain(bundle, row), saved=None, adr_inr=adr_inr)

    with right:
        lr = st.session_state.get("last_risk")
        with ui.card("bk_result"):
            if not lr:
                ui.card_title("🎯 Risk result")
                st.info("Fill in the reservation and click **Calculate Cancellation Risk**.")
                m = bundle["metrics"]
                st.caption(f"Model: gradient-boosted trees · accuracy {m['accuracy'] * 100:.1f}% · AUC {m['auc']:.3f} · "
                           f"trained on {bundle['n_rows']:,} completed reservations.")
            else:
                p, level = lr["p"], lr["level"]
                ui.card_title("🎯 Cancellation risk")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=p, number=dict(suffix="%", font=dict(size=44)),
                    gauge=dict(axis=dict(range=[0, 100]), bar=dict(color={"Low": "#13a366", "Medium": "#f0a020", "High": "#e5484d"}[level]),
                               steps=[dict(range=[0, cfg["low_risk_max"]], color="#d9f7e8"),
                                      dict(range=[cfg["low_risk_max"], cfg["high_risk_min"]], color="#fff0d1"),
                                      dict(range=[cfg["high_risk_min"], 100], color="#ffe0e2")])))
                ui.plot(ui.style_fig(fig, 250), "bk_gauge")
                st.markdown(f'<div style="text-align:center"><span class="badge {level.lower()}">{level} risk</span></div>', unsafe_allow_html=True)
                value = lr["adr_inr"] * lr["nights"]
                a, b, c = st.columns(3)
                a.metric("Stay value", an.inr(value))
                b.metric("Revenue at risk", an.inr(value * p / 100))
                c.metric("Nights", lr["nights"])
                st.markdown("**What drives this score?**")
                e = lr["expl"]
                fig = go.Figure(go.Bar(x=e["impact"], y=e["feature"], orientation="h",
                                       marker_color=["#e5484d" if v > 0 else "#13a366" for v in e["impact"]],
                                       text=[f"{v:+.1f} pp" for v in e["impact"]], textposition="outside"))
                fig.update_layout(xaxis_title="Impact on cancellation probability (percentage points)")
                ui.plot(ui.style_fig(fig, 280), "bk_expl")
                st.caption("Red = pushes risk up compared with a typical booking, green = pulls it down.")
                st.markdown("**Recommended actions**")
                for r in _recommendations(lr["row"], p, level, value):
                    st.markdown(f'<div class="reco">{r}</div>', unsafe_allow_html=True)
                st.write("")
                if lr.get("saved"):
                    st.success(f"Saved as **{lr['saved']}** – it now appears in the dashboards (extend the period filter if needed).")
                elif ui.stretch(st.button, "💾 Save booking to database", key="bk_save", type="primary"):
                    lr["saved"] = data_loader.append_booking(lr["record"])
                    core.clear_data_cache()
                    st.rerun()

    added = data_loader.read_added()
    with ui.card("bk_recent"):
        ui.card_title("🗂 Recently added bookings")
        if added.empty:
            st.caption("No bookings added yet.")
        else:
            show = added.tail(10).iloc[::-1][["booking_id", "guest_name", "hotel", "arrival_date_year", "arrival_date_month",
                                              "arrival_date_day_of_month", "lead_time", "market_segment", "risk_score", "risk_level", "created_at"]]
            ui.table(show, column_config={"risk_score": st.column_config.NumberColumn("Risk %", format="%.1f")})
