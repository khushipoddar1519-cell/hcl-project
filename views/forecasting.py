"""Demand Forecasting."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import analytics as an, components as ui, config, core

DEFAULTS = {"metric": "Net bookings (non-cancelled)", "horizon": 6, "adj": 0, "band": True, "hotel": "All"}


def _fmt(metric_col, v):
    if metric_col == "revenue":
        return an.inr_short(v)
    if metric_col == "adr":
        return an.inr(v)
    return an.indian(v)


def render(user):
    df_all = core.data()
    ui.page_header("Demand Forecasting", "Project future demand, revenue and cancellations from historical seasonality and trend.")
    body({"all": df_all}, key="fc")


def body(ctx, key="fc"):
    df_all = ctx["all"]
    p = st.session_state.setdefault(f"{key}_params", dict(DEFAULTS))
    with ui.card(f"{key}_form"):
        with st.form(f"{key}_form_widget"):
            c = st.columns([2.3, 1.6, 1.8, 2, 1.3, 1.2])
            metric = c[0].selectbox("Forecast metric", list(an.METRIC_COLS), index=list(an.METRIC_COLS).index(p["metric"]))
            hotel = c[1].selectbox("Hotel", ["All"] + sorted(df_all["hotel"].unique()), index=(["All"] + sorted(df_all["hotel"].unique())).index(p["hotel"]))
            horizon = c[2].select_slider("Months ahead", options=[3, 6, 9, 12, 18, 24], value=p["horizon"])
            adj = c[3].slider("Scenario adjustment (%)", -30, 30, p["adj"], help="Add an optimistic / pessimistic overlay on top of the statistical forecast.")
            band = c[4].checkbox("Confidence band", value=p["band"])
            c[5].write("")
            run = ui.stretch(st.form_submit_button, "Run Forecast", type="primary")
        if run:
            p.update(metric=metric, hotel=hotel, horizon=horizon, adj=adj, band=band)

    col = an.METRIC_COLS[p["metric"]]
    base = df_all if p["hotel"] == "All" else df_all[df_all["hotel"] == p["hotel"]]
    m = an.monthly(base).set_index("month_start")
    if len(m) < 6:
        st.warning("At least 6 months of history are needed to forecast.")
        return
    with st.spinner("Running forecast…"):
        fc, seas, fitted = an.forecast_series(m[col], p["horizon"], p["adj"])
    hist = m[col]
    h = p["horizon"]
    prev_same = hist.tail(h)
    agg = np.mean if col == "adr" else np.sum
    f_total, prev_total = agg(fc["forecast"]), agg(prev_same)
    chg = an.pct_change(f_total, prev_total)
    peak = fc.loc[fc["forecast"].idxmax()]
    low = fc.loc[fc["forecast"].idxmin()]

    k = st.columns(4)
    with k[0]:
        ui.kpi_card(f"Next month ({fc['month_start'].iloc[0]:%b %Y})", _fmt(col, fc["forecast"].iloc[0]), None, "blue", "calendar", small=True)
    with k[1]:
        lbl = "Average" if col == "adr" else "Total"
        ui.kpi_card(f"{lbl} – next {h} months", _fmt(col, f_total),
                    ui.delta_html(chg, "down" if col == "cancelled" else "up", f"vs last {h} months"), "teal", "trend", small=True)
    with k[2]:
        ui.kpi_card("Peak month", f"{peak['month_start']:%b %Y}", f'<div class="dl"><span>{_fmt(col, peak["forecast"])}</span></div>', "green", "arrowup", small=True)
    with k[3]:
        ui.kpi_card("Lowest month", f"{low['month_start']:%b %Y}", f'<div class="dl"><span>{_fmt(col, low["forecast"])}</span></div>', "orange", "alert", small=True)

    with ui.card(f"{key}_chart"):
        ui.card_title(f"{p['metric']} – history & {h}-month forecast",
                      f"Hotel: {p['hotel']} · scenario {p['adj']:+d}% · dataset ends {hist.index.max():%b %Y}")
        fig = go.Figure()
        fig.add_scatter(x=hist.index, y=hist.values, name="Actual", mode="lines+markers", line=dict(color=config.BLUE, width=3))
        fig.add_scatter(x=fitted.index, y=fitted.values, name="Model fit", mode="lines", line=dict(color="rgba(120,140,150,.6)", width=1.5, dash="dot"))
        x_fc = [hist.index.max()] + list(fc["month_start"])
        y_fc = [hist.values[-1]] + list(fc["forecast"])
        if p["band"]:
            fig.add_scatter(x=list(fc["month_start"]) + list(fc["month_start"])[::-1],
                            y=list(fc["upper"]) + list(fc["lower"])[::-1], fill="toself",
                            fillcolor="rgba(139,108,240,.15)", line=dict(width=0), name="80% range", hoverinfo="skip")
        fig.add_scatter(x=x_fc, y=y_fc, name="Forecast", mode="lines+markers", line=dict(color=config.PURPLE, width=3, dash="dash"),
                        marker=dict(size=8))
        ui.plot(ui.style_fig(fig, 400), f"{key}_fig")

    c1, c2 = st.columns([1, 1])
    with c1, ui.card(f"{key}_tbl"):
        ui.card_title("Forecast table")
        out = fc.copy()
        out["Month"] = out["month_start"].dt.strftime("%b %Y")
        out = out.rename(columns={"forecast": "Forecast", "lower": "Low", "upper": "High"})[["Month", "Forecast", "Low", "High"]]
        ui.table(out.round(0))
        st.download_button("⬇ Download forecast (CSV)", out.to_csv(index=False).encode(), "demand_forecast.csv", "text/csv", key=f"{key}_dl")
    with c2, ui.card(f"{key}_seas"):
        ui.card_title("Seasonality index", "Above 1.0 = busier than an average month.")
        s = pd.DataFrame({"month": config.MONTH_ABBR, "index": seas.values})
        fig = px.bar(s, x="month", y="index", color="index", color_continuous_scale=["#bfe9f3", "#19c1ad", "#0b6f68"])
        fig.add_hline(y=1.0, line_dash="dot", line_color="#7a8f94")
        fig.update_coloraxes(showscale=False)
        ui.plot(ui.style_fig(fig, 300), f"{key}_seas_fig")

    with ui.card(f"{key}_yoy"):
        ui.card_title("Year-over-year comparison", "Each line is a calendar year of actuals.")
        t = m.reset_index()
        t["year"] = t["month_start"].dt.year.astype(str)
        t["month"] = t["month_start"].dt.month
        fig = px.line(t, x="month", y=col, color="year", markers=True, color_discrete_sequence=[config.BLUE, config.PINK, config.GREEN, config.ORANGE])
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=config.MONTH_ABBR)
        ui.plot(ui.style_fig(fig, 320), f"{key}_yoy_fig")
