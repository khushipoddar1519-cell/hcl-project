"""Hotel Analytics – Cancellation & Revenue Management  (run with:  streamlit run app.py)"""
import streamlit as st

st.set_page_config(page_title="Hotel Analytics", page_icon="frontend/favicon.svg", layout="wide",
                   initial_sidebar_state="expanded")

from modules import components as ui, config, core, styles          # noqa: E402
from views import (admin_dashboard, admin_analytics, booking, cancellation, data_management,  # noqa: E402
                   forecasting, home, login, reports, revenue, segments, settings_page)

USER_NAV = [
    ("home", "Home", "home"),
    ("cancel", "Cancellation Analysis", "bar_chart"),
    ("forecast", "Demand Forecasting", "trending_up"),
    ("revenue", "Revenue Analysis", "database"),
    ("segments", "Room & Segment Analysis", "grid_view"),
    ("booking", "Add Booking & Risk", "add_circle"),
    ("reports", "Reports", "description"),
]
ADMIN_NAV = [
    ("dashboard", "Dashboard", "dashboard"),
    ("data", "Data Management", "database"),
    ("analytics", "Analytics", "show_chart"),
    ("booking", "Add Booking & Risk", "add_circle"),
    ("reports", "Reports", "description"),
    ("settings", "Settings", "settings"),
]
PAGES = {
    "home": home.render, "cancel": cancellation.render, "forecast": forecasting.render,
    "revenue": revenue.render, "segments": segments.render, "booking": booking.render,
    "reports": reports.render, "dashboard": admin_dashboard.render, "data": data_management.render,
    "analytics": admin_analytics.render, "settings": settings_page.render,
}


def logout():
    for k in ("auth", "page", "flt_range", "flt_hotel", "last_risk", "fc_params"):
        st.session_state.pop(k, None)


def main():
    user = st.session_state.get("auth")
    styles.inject(hide_sidebar=user is None)
    if user is None:
        login.render()
        return

    is_admin = user["role"] == "Administrator"
    nav = ADMIN_NAV if is_admin else USER_NAV
    allowed = [n[0] for n in nav]
    if st.session_state.get("page") not in allowed:
        st.session_state["page"] = allowed[0]
    page = st.session_state["page"]

    # ---------------- top bar (brand + user menu)
    c1, c2 = st.columns([8, 2.3])
    c1.markdown(f'<div class="brand">{ui.LOGO_SVG}{config.APP_NAME}</div>',
                unsafe_allow_html=True)
    with c2:
        with st.popover(f"{user['name']}  ·  {user['role']}", icon=":material/account_circle:",
                        **({"width": "stretch"} if ui._ver() >= (1, 50) else {"use_container_width": True})):
            st.markdown(f"**{user['name']}**  \n{user['email']}  \nRole: `{user['role']}`")
            st.button("🚪 Logout", key="logout_btn", icon=":material/logout:", on_click=logout, type="primary")
            st.button("🔄 Login another account", key="switch_acc_btn", icon=":material/switch_account:", on_click=logout)

    # ---------------- sidebar navigation
    with st.sidebar:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        for pid, label, ico in nav:
            ui.go_button(label, pid, key=f"nav_{pid}", icon_name=f":material/{ico}:",
                         type="primary" if pid == page else "secondary")
        df = core.data()
        st.divider()
        st.caption(f"📦 {len(df):,} bookings · {df['arrival_date'].min():%b %Y} – {df['arrival_date'].max():%b %Y}")

    PAGES[page](user)


main()
