"""Room & Segment Analysis."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import analytics as an, components as ui, config, core

DIMS = {
    "Market segment": "segment", "Room category": "room_group", "Room type (A–L)": "reserved_room_type",
    "Distribution channel": "distribution_channel", "Customer type": "customer_type",
    "Meal plan": "meal", "Hotel": "hotel", "Deposit type": "deposit_type",
}


def render(user):
    df_all = core.data()
    ui.page_header("Room & Segment Analysis", "Compare performance across room categories, market segments and channels.")
    ctx = ui.filter_bar(df_all, "sg")
    if ui.empty_guard(ctx):
        return
    body(ctx)


def body(ctx, key="sg"):
    df = ctx["df"]
    seg = an.group_stats(df, "segment")
    room = an.group_stats(df, "room_group")
    best_seg = seg.sort_values("revenue", ascending=False).iloc[0]
    worst_seg = seg[seg["bookings"] >= 500].sort_values("cancel_rate", ascending=False).iloc[0]
    best_room = room.sort_values("revenue", ascending=False).iloc[0]
    changed = df["room_changed"].mean() * 100
    c = st.columns(4)
    with c[0]:
        ui.kpi_card("Top segment (revenue)", best_seg["segment"], f'<div class="dl up">{best_seg["revenue_share"]:.1f}% <span>of revenue</span></div>', "teal", "users", small=True)
    with c[1]:
        ui.kpi_card("Riskiest segment", worst_seg["segment"], f'<div class="dl down">{worst_seg["cancel_rate"]:.1f}% <span>cancel rate</span></div>', "red", "alert", small=True)
    with c[2]:
        ui.kpi_card("Top room category", best_room["room_group"], f'<div class="dl up">{best_room["revenue_share"]:.1f}% <span>of revenue</span></div>', "purple", "bed", small=True)
    with c[3]:
        ui.kpi_card("Guests given a different room", f"{changed:.1f}%", '<div class="dl"><span>reserved ≠ assigned room</span></div>', "orange", "bed", small=True)

    t1, t2, t3 = st.tabs(["🎯 Explorer", "🛏 Room categories", "🔁 Room reassignment"])
    with t1:
        with ui.card(f"{key}_explore"):
            a, b = st.columns(2)
            dim = a.selectbox("Group by", list(DIMS), key=f"{key}_dim")
            metric = b.selectbox("Metric", ["Revenue", "Bookings", "Cancellation rate", "ADR"], key=f"{key}_metric")
            col = DIMS[dim]
            g = an.group_stats(df, col)
            mcol = {"Revenue": "revenue", "Bookings": "bookings", "Cancellation rate": "cancel_rate", "ADR": "adr"}[metric]
            g = g.sort_values(mcol, ascending=False)
            fig = px.bar(g, x=col, y=mcol, color=mcol, color_continuous_scale="Tealgrn", labels={col: "", mcol: metric})
            fig.update_coloraxes(showscale=False)
            ui.plot(ui.style_fig(fig, 340), f"{key}_ex_fig")
        with ui.card(f"{key}_bubble"):
            ui.card_title(f"{dim}: volume vs cancellation vs revenue", "Bubble size = revenue.")
            gg = g[g["bookings"] > 0]
            fig = px.scatter(gg, x="bookings", y="cancel_rate", size=gg["revenue"].clip(lower=1), color=col, hover_name=col,
                             size_max=55, labels={"bookings": "Bookings", "cancel_rate": "Cancellation %"})
            ui.plot(ui.style_fig(fig, 360), f"{key}_bub_fig")
        with ui.card(f"{key}_tbl"):
            ui.card_title("Detail table")
            out = g.rename(columns={col: dim, "bookings": "Bookings", "cancelled": "Cancelled", "cancel_rate": "Cancel %",
                                    "revenue": "Revenue (₹)", "lost_revenue": "Lost (₹)", "adr": "ADR (₹)", "share": "Booking share %"})
            ui.table(out[[dim, "Bookings", "Cancelled", "Cancel %", "Revenue (₹)", "Lost (₹)", "ADR (₹)", "Booking share %"]],
                     column_config={"Cancel %": st.column_config.NumberColumn(format="%.1f%%"),
                                    "Booking share %": st.column_config.NumberColumn(format="%.1f%%"),
                                    "Revenue (₹)": st.column_config.NumberColumn(format="₹ %.0f"),
                                    "Lost (₹)": st.column_config.NumberColumn(format="₹ %.0f"),
                                    "ADR (₹)": st.column_config.NumberColumn(format="₹ %.0f")})
    with t2:
        c1, c2 = st.columns(2)
        with c1, ui.card(f"{key}_rd"):
            ui.card_title("Revenue share by room category")
            r = room.set_index("room_group").reindex([x for x in config.ROOM_ORDER if x in set(room["room_group"])]).reset_index()
            fig = go.Figure(go.Pie(labels=r["room_group"], values=r["revenue"], hole=.6, sort=False,
                                   marker=dict(colors=[config.ROOM_COLORS[x] for x in r["room_group"]])))
            fig.add_annotation(text=f"<b>{an.inr_short(r['revenue'].sum())}</b>", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
            ui.plot(ui.style_fig(fig, 340), f"{key}_rd_fig")
        with c2, ui.card(f"{key}_rc"):
            ui.card_title("Cancellation rate & ADR by room category")
            fig = go.Figure()
            fig.add_bar(x=r["room_group"], y=r["cancel_rate"], name="Cancel %", marker_color=config.PINK, text=r["cancel_rate"].map(lambda v: f"{v:.1f}%"))
            fig.add_scatter(x=r["room_group"], y=r["adr"], name="ADR (₹)", yaxis="y2", mode="lines+markers", line=dict(color=config.PURPLE, width=3))
            fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, title="ADR (₹)"), yaxis_title="Cancel %")
            ui.plot(ui.style_fig(fig, 340), f"{key}_rc_fig")
        with ui.card(f"{key}_rs"):
            ui.card_title("Room category × market segment – cancellation rate")
            p = df.pivot_table(index="room_group", columns="segment", values="is_canceled", aggfunc="mean") * 100
            n = df.pivot_table(index="room_group", columns="segment", values="is_canceled", aggfunc="size")
            p = p.where(n >= 30).reindex([x for x in config.ROOM_ORDER if x in p.index])
            fig = go.Figure(go.Heatmap(z=p.values, x=list(p.columns), y=list(p.index), colorscale="RdYlGn_r", zmin=0, zmax=100,
                                       text=np.round(p.values, 0), texttemplate="%{text}"))
            ui.plot(ui.style_fig(fig, 320), f"{key}_rs_fig")
    with t3:
        with ui.card(f"{key}_chg"):
            ui.card_title("Does getting a different room affect cancellations?")
            g = df.assign(Room=df["room_changed"].map({0: "Assigned = reserved", 1: "Different room"})) \
                  .groupby("Room").agg(bookings=("is_canceled", "size"), rate=("is_canceled", "mean"),
                                       adr=("adr_inr", "mean")).reset_index()
            g["rate"] *= 100
            a, b = st.columns(2)
            fig = px.bar(g, x="Room", y="bookings", color="Room", color_discrete_sequence=[config.TEAL, config.ORANGE], title="Bookings")
            fig.update_layout(showlegend=False)
            with a:
                ui.plot(ui.style_fig(fig, 280), f"{key}_chg1")
            fig = px.bar(g, x="Room", y="rate", color="Room", color_discrete_sequence=[config.TEAL, config.ORANGE], title="Cancellation %",
                         text=g["rate"].map(lambda v: f"{v:.1f}%"))
            fig.update_layout(showlegend=False)
            with b:
                ui.plot(ui.style_fig(fig, 280), f"{key}_chg2")
            st.caption("Guests who are moved to a different room than the one they reserved usually cancel less (they are mostly bookings that reached check-in).")
