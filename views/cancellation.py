"""Cancellation Analysis."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modules import analytics as an, components as ui, config, core

DRIVERS = {
    "Lead time": "lead_bucket", "Deposit type": "deposit_type", "Customer type": "customer_type",
    "Special requests": "req_grp", "Previous cancellations": "prev_canc_grp", "Repeat guest": "repeat_grp",
    "Booking changes": "chg_grp", "Meal plan": "meal", "Distribution channel": "distribution_channel",
    "Room type (reserved)": "room_group", "Room reassigned at check-in": "room_changed_grp",
}


def _derive(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["lead_bucket"] = an.lead_bucket(d["lead_time"])
    d["req_grp"] = d["total_of_special_requests"].clip(upper=3).astype(int).astype(str).replace({"3": "3+"})
    d["prev_canc_grp"] = d["previous_cancellations"].clip(upper=3).astype(int).astype(str).replace({"3": "3+"})
    d["chg_grp"] = d["booking_changes"].clip(upper=3).astype(int).astype(str).replace({"3": "3+"})
    d["repeat_grp"] = d["is_repeated_guest"].map({0: "New guest", 1: "Repeat guest"})
    d["room_changed_grp"] = d["room_changed"].map({0: "Same room", 1: "Different room"})
    return d


def render(user):
    df_all = core.data()
    ui.page_header("Cancellation Analysis", "Understand when, where and why bookings get cancelled.")
    ctx = ui.filter_bar(df_all, "cx")
    if ui.empty_guard(ctx):
        return
    body(ctx)


def body(ctx, key="cx"):
    df = ctx["df"]
    cur, dl = an.compare(ctx["all"], ctx["start"], ctx["end"], "prev", ctx["hotel"])
    kept_lead = df.loc[df["is_canceled"] == 0, "lead_time"].mean()
    canc_lead = df.loc[df["is_canceled"] == 1, "lead_time"].mean()
    c = st.columns(4)
    with c[0]:
        ui.kpi_card("Cancellation Rate", an.pct(cur["cancel_rate"]), ui.delta_html(dl["cancel_rate"], "down", "vs. previous period"), "red", "xcircle", small=True)
    with c[1]:
        ui.kpi_card("Cancelled Bookings", an.indian(cur["cancelled"]), ui.delta_html(dl["cancelled"], "down", "vs. previous period"), "orange", "alert", small=True)
    with c[2]:
        ui.kpi_card("Revenue Lost", an.inr_short(cur["lost_revenue"]), ui.delta_html(dl["lost_revenue"], "down", "vs. previous period"), "purple", "wallet", small=True, tooltip=an.inr(cur["lost_revenue"]))
    with c[3]:
        ui.kpi_card("Avg Lead Time (cancelled)", f"{canc_lead:.0f} days",
                    f'<div class="dl"><span>vs {kept_lead:.0f} days for kept bookings</span></div>', "teal", "calendar", small=True)

    d = _derive(df)
    t1, t2, t3, t4 = st.tabs(["📈 Trend & Seasonality", "🔍 Cancellation Drivers", "🧩 Segments", "🌍 Geography"])

    with t1:
        m = an.monthly(df)
        with ui.card(f"{key}_trend"):
            ui.card_title("Bookings vs Cancellation Rate by Month")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_bar(x=m["month_start"], y=m["net_bookings"], name="Kept bookings", marker_color=config.BLUE)
            fig.add_bar(x=m["month_start"], y=m["cancelled"], name="Cancelled", marker_color=config.PINK)
            fig.add_scatter(x=m["month_start"], y=m["cancel_rate"], name="Cancellation rate %", mode="lines+markers",
                            line=dict(color=config.PURPLE, width=3), secondary_y=True)
            fig.update_layout(barmode="stack")
            fig.update_yaxes(title_text="Bookings", secondary_y=False)
            fig.update_yaxes(title_text="Cancellation %", secondary_y=True, showgrid=False, rangemode="tozero")
            ui.plot(ui.style_fig(fig, 380), f"{key}_trend_fig")
        with ui.card(f"{key}_season"):
            ui.card_title("Seasonality – cancellation rate by arrival month")
            s = d.groupby("month_num").agg(r=("is_canceled", "mean"), n=("is_canceled", "size")).reset_index()
            s["month"] = s["month_num"].map(lambda x: config.MONTH_ABBR[x - 1])
            s["r"] *= 100
            fig = px.bar(s, x="month", y="r", color="r", color_continuous_scale=["#9be7da", "#ffd27a", "#ff6b6b"],
                         hover_data={"n": True, "r": ":.1f"}, labels={"r": "Cancellation %", "month": ""})
            fig.update_coloraxes(showscale=False)
            ui.plot(ui.style_fig(fig, 300), f"{key}_season_fig")

    with t2:
        with ui.card(f"{key}_drv"):
            pick = st.selectbox("Analyse cancellation rate by", list(DRIVERS), key=f"{key}_driver")
            col = DRIVERS[pick]
            g = d.groupby(col, observed=True).agg(bookings=("is_canceled", "size"), cancelled=("is_canceled", "sum")).reset_index()
            g["rate"] = g["cancelled"] / g["bookings"] * 100
            g[col] = g[col].astype(str)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_bar(x=g[col], y=g["bookings"], name="Bookings", marker_color="rgba(77,163,255,.45)")
            fig.add_scatter(x=g[col], y=g["rate"], name="Cancellation %", mode="lines+markers+text",
                            text=[f"{v:.0f}%" for v in g["rate"]], textposition="top center",
                            line=dict(color=config.RED, width=3), secondary_y=True)
            fig.update_yaxes(title_text="Bookings", secondary_y=False)
            fig.update_yaxes(title_text="Cancellation %", secondary_y=True, showgrid=False, range=[0, 105])
            ui.plot(ui.style_fig(fig, 380), f"{key}_drv_fig")
            ui.table(g.rename(columns={col: pick, "bookings": "Bookings", "cancelled": "Cancelled", "rate": "Cancel %"}),
                     column_config={"Cancel %": st.column_config.NumberColumn(format="%.1f%%")})
        with ui.card(f"{key}_lead"):
            ui.card_title("Lead-time distribution", "Cancelled bookings are typically made much further in advance.")
            samp = d[d["lead_time"] <= 500]
            fig = go.Figure()
            fig.add_histogram(x=samp.loc[samp["is_canceled"] == 0, "lead_time"], name="Kept", marker_color=config.BLUE, opacity=.65, nbinsx=50)
            fig.add_histogram(x=samp.loc[samp["is_canceled"] == 1, "lead_time"], name="Cancelled", marker_color=config.PINK, opacity=.65, nbinsx=50)
            fig.update_layout(barmode="overlay", xaxis_title="Lead time (days)", yaxis_title="Bookings")
            ui.plot(ui.style_fig(fig, 300), f"{key}_lead_fig")

    with t3:
        c1, c2 = st.columns(2)
        with c1, ui.card(f"{key}_heat"):
            ui.card_title("Segment × Channel cancellation heat-map")
            p = d.pivot_table(index="segment", columns="distribution_channel", values="is_canceled", aggfunc="mean") * 100
            n = d.pivot_table(index="segment", columns="distribution_channel", values="is_canceled", aggfunc="size")
            p = p.where(n >= 30)
            fig = go.Figure(go.Heatmap(z=p.values, x=list(p.columns), y=list(p.index), colorscale="RdYlGn_r",
                                       zmin=0, zmax=100, text=np.round(p.values, 0), texttemplate="%{text}",
                                       colorbar=dict(title="%")))
            ui.plot(ui.style_fig(fig, 360), f"{key}_heat_fig")
        with c2, ui.card(f"{key}_seg"):
            ui.card_title("Cancellation rate by market segment")
            g = an.group_stats(d, "segment").sort_values("cancel_rate")
            fig = px.bar(g, x="cancel_rate", y="segment", orientation="h", color="cancel_rate",
                         color_continuous_scale=["#9be7da", "#ffd27a", "#ff6b6b"], text=g["cancel_rate"].map(lambda v: f"{v:.1f}%"),
                         labels={"cancel_rate": "Cancellation %", "segment": ""})
            fig.update_coloraxes(showscale=False)
            ui.plot(ui.style_fig(fig, 360), f"{key}_seg_fig")
        with ui.card(f"{key}_hot"):
            ui.card_title("Hotel & customer type")
            a, b = st.columns(2)
            for col, area, ttl in (("hotel", a, "By hotel"), ("customer_type", b, "By customer type")):
                g = an.group_stats(d, col)
                fig = px.bar(g, x=col, y="cancel_rate", color=col, text=g["cancel_rate"].map(lambda v: f"{v:.1f}%"),
                             labels={"cancel_rate": "Cancellation %", col: ""}, color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(showlegend=False, title=ttl)
                with area:
                    ui.plot(ui.style_fig(fig, 300), f"{key}_{col}_fig")

    with t4:
        g = an.group_stats(d, "country")
        g = g[(g["bookings"] >= 100) & (g["country"] != "Unknown")]
        with ui.card(f"{key}_geo"):
            ui.card_title("Cancellation rate by guest country", "Countries with 100+ bookings in the selected period.")
            fig = px.choropleth(g, locations="country", color="cancel_rate", hover_name="country",
                                hover_data={"bookings": True, "cancel_rate": ":.1f"},
                                color_continuous_scale="RdYlGn_r", range_color=(0, 100),
                                labels={"cancel_rate": "Cancel %"})
            fig.update_geos(showframe=False, showcoastlines=False, bgcolor="rgba(0,0,0,0)")
            ui.plot(ui.style_fig(fig, 420), f"{key}_geo_fig")
        with ui.card(f"{key}_topc"):
            ui.card_title("Top 15 source countries")
            top = g.sort_values("bookings", ascending=False).head(15).copy()
            top["Country"] = top["country"].map(lambda c: f"{c} – {config.COUNTRY_NAMES.get(c, '')}".strip(" –"))
            ui.table(top[["Country", "bookings", "cancel_rate", "revenue"]].rename(
                columns={"bookings": "Bookings", "cancel_rate": "Cancel %", "revenue": "Revenue (₹)"}),
                column_config={"Cancel %": st.column_config.NumberColumn(format="%.1f%%"),
                               "Revenue (₹)": st.column_config.NumberColumn(format="₹ %.0f")})
