"""Home – welcome, KPIs, quick actions, recent insights."""
import streamlit as st

from modules import analytics as an, components as ui, core

_IC = {"cancel": ("xcircle", "red"), "demand": ("arrowup", "green"), "revenue": ("database", "purple")}


def _row_html(ins):
    ic, tone = _IC.get(ins["kind"], ("bulb", "teal"))
    return (f'<div class="ins"><div class="ci {tone}">{ui.icon(ic, 24)}</div>'
            f'<div><div class="tt">{ins["title"]}</div><div class="ds">{ins["desc"]}</div></div></div>')


@st.dialog("All insights", width="large")
def _all_insights(items):
    for it in items:
        c1, c2 = st.columns([10, 2])
        c1.markdown(_row_html(it), unsafe_allow_html=True)
        c2.button("Open", key=f"dlg_{it['title']}", on_click=ui.goto, args=(it["page"],))


def render(user):
    df_all = core.data()
    first = user["name"].split()[0]
    c1, c2 = st.columns([6, 3])
    with c1:
        ui.page_header(f"Welcome, {first}!", "Explore hotel booking insights and make data-driven decisions.")
    with c2:
        ctx = ui.filter_bar(df_all, "home", hotel=False, inline=True, label="Analysis period")

    cur, d = an.compare(df_all, ctx["start"], ctx["end"], "yoy")
    cols = st.columns(4)
    with cols[0]:
        ui.kpi_card("Total Bookings", an.indian(cur["bookings"]), ui.delta_html(d["bookings"], "up"),
                    "blue", "calendar")
    with cols[1]:
        ui.kpi_card("Cancelled Bookings", an.indian(cur["cancelled"]), ui.delta_html(d["cancelled"], "down"),
                    "green", "xcircle")
    with cols[2]:
        ui.kpi_card("Total Revenue", an.inr_short(cur["revenue"]), ui.delta_html(d["revenue"], "up"),
                    "teal", "database", tooltip=an.inr(cur["revenue"]))
    with cols[3]:
        ui.kpi_card("Avg. Daily Rate (ADR)", an.inr(cur["adr"]), ui.delta_html(d["adr"], "up"),
                    "orange", "chart")

    st.markdown('<div class="card-title" style="margin-top:1.1rem">Quick Actions</div>', unsafe_allow_html=True)
    with st.container(key="quick_grid"):
        a, b = st.columns(2)
        with a:
            ui.go_button("View Cancellation Trends", "cancel", "qa1", ":material/bar_chart:")
            ui.go_button("Analyze Revenue", "revenue", "qa3", ":material/database:")
        with b:
            ui.go_button("Run Demand Forecast", "forecast", "qa2", ":material/calendar_month:")
            ui.go_button("Explore Room & Segment Insights", "segments", "qa4", ":material/grid_view:")
        ui.go_button("Add a Booking & Check Cancellation Risk", "booking", "qa5", ":material/add_circle:")

    df_win = ctx["df"]
    items = an.insights(df_win, df_all)
    with ui.card("insights"):
        h1, h2 = st.columns([8, 1.3])
        h1.markdown('<div class="card-title">Recent Insights</div>', unsafe_allow_html=True)
        if h2.button("View All", key="ins_all", type="tertiary"):
            _all_insights(items)
        for i, it in enumerate(items[:3]):
            c1, c2 = st.columns([13, 1])
            c1.markdown(_row_html(it), unsafe_allow_html=True)
            c2.button("›", key=f"ins_{i}", on_click=ui.goto, args=(it["page"],), type="tertiary")
        if not items:
            st.info("Not enough data in this period to generate insights.")

    tip = an.tip(df_win)
    if tip:
        c1, c2 = st.columns([13, 1])
        c1.markdown(
            f'<div class="tipbox">{ui.icon("bulb", 30, "#2a8fb0")}<div><b>Tip:</b> Focus on reducing cancellations '
            f'from <b>{tip["segment"]}</b> segment to improve revenue by ~{tip["uplift"]:.0f}%. '
            f'<span style="color:#6b8a90;font-size:.8rem">(assumes a {tip["reduction"] * 100:.0f}% drop in that segment\'s cancellations)</span></div></div>',
            unsafe_allow_html=True)
        c2.button("›", key="tip_go", on_click=ui.goto, args=("cancel",), type="tertiary")
