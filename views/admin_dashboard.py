"""Admin – Analytics Dashboard (matches the right-hand screen of the reference design)."""
import plotly.graph_objects as go
import streamlit as st

from modules import analytics as an, components as ui, config, core


def render(user):
    df_all = core.data()
    c1, c2 = st.columns([6, 3])
    with c1:
        ui.page_header("Analytics Dashboard", "Executive overview of cancellations, revenue and demand.")
    with c2:
        ctx = ui.filter_bar(df_all, "ad", hotel=False, inline=True, label="Date range")
    df = ctx["df"]
    if ui.empty_guard(ctx):
        return
    cur, d = an.compare(df_all, ctx["start"], ctx["end"], "prev")

    k = st.columns(3)
    with k[0]:
        ui.kpi_card("Cancellation Rate", an.pct(cur["cancel_rate"]), ui.delta_html(d["cancel_rate"], "down", "vs. previous period"), "red", "xcircle", small=True)
    with k[1]:
        ui.kpi_card("Total Revenue", an.inr_short(cur["revenue"]), ui.delta_html(d["revenue"], "up", "vs. previous period"), "teal", "database", small=True, tooltip=an.inr(cur["revenue"]))
    with k[2]:
        ui.kpi_card("Avg. Daily Rate (ADR)", an.inr(cur["adr"]), ui.delta_html(d["adr"], "up", "vs. previous period"), "purple", "chart", small=True)

    m = an.monthly(df)
    with ui.card("ad_trend"):
        ui.card_title("Booking vs Cancellation Trend")
        fig = go.Figure()
        fig.add_bar(x=m["month_start"], y=m["bookings"], name="Bookings", marker_color=config.BLUE)
        fig.add_scatter(x=m["month_start"], y=m["cancelled"], name="Cancellations", mode="lines+markers",
                        line=dict(color=config.PINK, width=2.5), marker=dict(size=7))
        fig.update_xaxes(tickformat="%b %y")
        ui.plot(ui.style_fig(fig, 330), "ad_trend_fig")

    c1, c2 = st.columns(2)
    with c1, ui.card("ad_fc"):
        ui.card_title("Demand Forecast (Next 6 Months)")
        hist = an.monthly(ctx["all"])
        if len(hist) >= 6:
            fc, _, _ = an.forecast_series(hist.set_index("month_start")["net_bookings"], 6)
            tail = hist.tail(6)
            fig = go.Figure()
            fig.add_scatter(x=tail["month_start"], y=tail["net_bookings"], name="Actual", mode="lines+markers", line=dict(color=config.BLUE, width=2.5))
            fig.add_scatter(x=list(fc["month_start"]) + list(fc["month_start"])[::-1], y=list(fc["upper"]) + list(fc["lower"])[::-1],
                            fill="toself", fillcolor="rgba(139,108,240,.15)", line=dict(width=0), hoverinfo="skip", showlegend=False)
            fig.add_scatter(x=[tail["month_start"].iloc[-1]] + list(fc["month_start"]), y=[tail["net_bookings"].iloc[-1]] + list(fc["forecast"]),
                            name="Forecast", mode="lines+markers", line=dict(color=config.PURPLE, width=3), marker=dict(size=8))
            fig.update_xaxes(tickformat="%b")
            ui.plot(ui.style_fig(fig, 300), "ad_fc_fig")
        else:
            st.info("Not enough history to forecast.")
    with c2, ui.card("ad_room"):
        ui.card_title("Revenue by Room Type")
        g = an.group_stats(df, "room_group")
        g["order"] = g["room_group"].map({r: i for i, r in enumerate(config.ROOM_ORDER)})
        g = g.sort_values("order")
        fig = go.Figure(go.Pie(labels=g["room_group"], values=g["revenue"], hole=.62, sort=False,
                               marker=dict(colors=[config.ROOM_COLORS.get(r, "#999") for r in g["room_group"]]),
                               textinfo="percent"))
        fig.add_annotation(text=f"<b>{an.inr_short(g['revenue'].sum())}</b><br><span style='font-size:11px'>Total Revenue</span>", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        fig.update_layout(legend=dict(orientation="v", x=1.0, y=.5))
        ui.plot(ui.style_fig(fig, 300), "ad_room_fig")

    with ui.card("ad_seg"):
        ui.card_title("Top Market Segments by Revenue")
        t = an.top_with_others(an.group_stats(df, "segment"), "segment", 4).rename(columns={"segment": "Market Segment"})
        t = t.rename(columns={"bookings": "Bookings", "revenue": "Revenue (₹)", "share": "Share"})
        ui.html_table(t, {"Bookings": lambda v: an.indian(v), "Revenue (₹)": lambda v: an.indian(v), "Share": lambda v: f"{v:.0f}%"},
                      num_cols=("Bookings", "Revenue (₹)", "Share"))
