"""Revenue Analysis."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modules import analytics as an, components as ui, config, core


def render(user):
    df_all = core.data()
    ui.page_header("Revenue Analysis", "Track revenue, ADR and the money lost to cancellations.")
    ctx = ui.filter_bar(df_all, "rv")
    if ui.empty_guard(ctx):
        return
    body(ctx)


def body(ctx, key="rv"):
    df = ctx["df"]
    cur, dl = an.compare(ctx["all"], ctx["start"], ctx["end"], "yoy", ctx["hotel"])
    c = st.columns(4)
    with c[0]:
        ui.kpi_card("Total Revenue", an.inr_short(cur["revenue"]), ui.delta_html(dl["revenue"], "up"), "teal", "database", small=True, tooltip=an.inr(cur["revenue"]))
    with c[1]:
        ui.kpi_card("Avg. Daily Rate (ADR)", an.inr(cur["adr"]), ui.delta_html(dl["adr"], "up"), "orange", "chart", small=True)
    with c[2]:
        ui.kpi_card("Revenue / Booking", an.inr(cur["rev_per_booking"]), ui.delta_html(dl["rev_per_booking"], "up"), "blue", "wallet", small=True)
    with c[3]:
        ui.kpi_card("Revenue Lost (cancellations)", an.inr_short(cur["lost_revenue"]),
                    f'<div class="dl"><span>{cur["realisation"]:.1f}% of potential revenue realised</span></div>', "red", "xcircle", small=True, tooltip=an.inr(cur["lost_revenue"]))

    m = an.monthly(df)
    with ui.card(f"{key}_trend"):
        ui.card_title("Monthly revenue & ADR")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(x=m["month_start"], y=m["revenue"], name="Revenue (₹)", marker_color=config.TEAL)
        fig.add_bar(x=m["month_start"], y=m["lost_revenue"], name="Lost to cancellations (₹)", marker_color="rgba(255,107,154,.55)")
        fig.add_scatter(x=m["month_start"], y=m["adr"], name="ADR (₹)", mode="lines+markers", line=dict(color=config.ORANGE, width=3), secondary_y=True)
        fig.update_layout(barmode="group")
        fig.update_yaxes(title_text="Revenue (₹)", secondary_y=False)
        fig.update_yaxes(title_text="ADR (₹)", secondary_y=True, showgrid=False, rangemode="tozero")
        ui.plot(ui.style_fig(fig, 380), f"{key}_trend_fig")

    c1, c2 = st.columns(2)
    with c1, ui.card(f"{key}_hotel"):
        ui.card_title("Revenue by hotel")
        t = df.groupby(["month_start", "hotel"])["revenue"].sum().reset_index()
        fig = px.area(t, x="month_start", y="revenue", color="hotel", color_discrete_sequence=[config.BLUE, config.GREEN], labels={"month_start": "", "revenue": "Revenue (₹)"})
        ui.plot(ui.style_fig(fig, 320), f"{key}_hotel_fig")
    with c2, ui.card(f"{key}_room"):
        ui.card_title("Revenue by room type")
        g = an.group_stats(df, "room_group")
        fig = go.Figure(go.Pie(labels=g["room_group"], values=g["revenue"], hole=.62, sort=False,
                               marker=dict(colors=[config.ROOM_COLORS.get(r, "#999") for r in g["room_group"]])))
        fig.add_annotation(text=f"<b>{an.inr_short(g['revenue'].sum())}</b><br><span style='font-size:11px'>Total Revenue</span>", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        ui.plot(ui.style_fig(fig, 320), f"{key}_room_fig")

    c1, c2 = st.columns(2)
    with c1, ui.card(f"{key}_seg"):
        ui.card_title("Revenue & lost revenue by market segment")
        g = an.group_stats(df, "segment").sort_values("revenue")
        fig = go.Figure()
        fig.add_bar(y=g["segment"], x=g["revenue"], orientation="h", name="Revenue", marker_color=config.TEAL)
        fig.add_bar(y=g["segment"], x=g["lost_revenue"], orientation="h", name="Lost", marker_color="rgba(255,107,154,.6)")
        fig.update_layout(barmode="group")
        ui.plot(ui.style_fig(fig, 340), f"{key}_seg_fig")
    with c2, ui.card(f"{key}_adr"):
        ui.card_title("ADR heat-map (year × month)")
        t = m.copy()
        t["year"] = t["month_start"].dt.year
        t["mon"] = t["month_start"].dt.month
        p = t.pivot_table(index="year", columns="mon", values="adr")
        p = p.reindex(columns=range(1, 13))
        fig = go.Figure(go.Heatmap(z=p.values, x=config.MONTH_ABBR, y=[str(y) for y in p.index], colorscale="Tealgrn",
                                   text=np.round(p.values, 0), texttemplate="%{text:,.0f}"))
        ui.plot(ui.style_fig(fig, 340), f"{key}_adr_fig")

    c1, c2 = st.columns(2)
    with c1, ui.card(f"{key}_cty"):
        ui.card_title("Top 10 countries by revenue")
        g = an.group_stats(df, "country").sort_values("revenue", ascending=False).head(10)
        fig = px.bar(g, x="country", y="revenue", color="revenue", color_continuous_scale="Tealgrn", labels={"revenue": "Revenue (₹)", "country": ""})
        fig.update_coloraxes(showscale=False)
        ui.plot(ui.style_fig(fig, 320), f"{key}_cty_fig")
    with c2, ui.card(f"{key}_wk"):
        ui.card_title("Average stay value by customer type")
        g = an.group_stats(df, "customer_type")
        fig = px.bar(g, x="customer_type", y="adr", color="customer_type", text=g["adr"].map(lambda v: f"₹{v:,.0f}"),
                     color_discrete_sequence=px.colors.qualitative.Set2, labels={"adr": "ADR (₹)", "customer_type": ""})
        fig.update_layout(showlegend=False)
        ui.plot(ui.style_fig(fig, 320), f"{key}_wk_fig")

    with ui.card(f"{key}_sim"):
        ui.card_title("💡 Revenue opportunity simulator", "Estimate the upside of better cancellation control and pricing.")
        a, b = st.columns(2)
        red = a.slider("Reduce cancellations by (%)", 0, 50, 15, key=f"{key}_red")
        up = b.slider("Increase ADR by (%)", 0, 20, 3, key=f"{key}_up")
        recovered = cur["lost_revenue"] * red / 100
        uplift = (cur["revenue"] + recovered) * up / 100
        s = st.columns(3)
        s[0].metric("Recovered from cancellations", an.inr_short(recovered))
        s[1].metric("Extra from ADR uplift", an.inr_short(uplift))
        s[2].metric("Total revenue opportunity", an.inr_short(recovered + uplift),
                    f"+{(recovered + uplift) / cur['revenue'] * 100:.1f}%" if cur["revenue"] else None)
