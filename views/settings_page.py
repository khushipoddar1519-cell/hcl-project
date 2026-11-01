"""Admin – Settings."""
import pandas as pd
import streamlit as st

from modules import auth, components as ui, config, core, data_loader, settings


def render(user):
    ui.page_header("Settings", "Configure the app, manage users and maintain the model.")
    cfg = settings.load()
    t1, t2, t3, t4 = st.tabs(["⚙️ General", "👥 Users", "🤖 Model", "🧹 Maintenance"])

    with t1:
        with ui.card("st_general"):
            with st.form("st_form"):
                c = st.columns(2)
                name = c[0].text_input("Hotel / organisation name", cfg["hotel_name"])
                fx = c[1].number_input("EUR → INR conversion rate", 1.0, 500.0, float(cfg["eur_to_inr"]), step=0.5,
                                       help="The dataset ADR is in EUR. All revenue is shown in ₹ using this rate.")
                c = st.columns(3)
                low = c[0].number_input("Low-risk below (%)", 1, 90, int(cfg["low_risk_max"]))
                high = c[1].number_input("High-risk from (%)", 2, 99, int(cfg["high_risk_min"]))
                win = c[2].number_input("Default period (months)", 1, 36, int(cfg["window_months"]))
                if ui.stretch(st.form_submit_button, "Save settings", type="primary"):
                    if low >= high:
                        st.error("Low-risk threshold must be below the high-risk threshold.")
                    else:
                        settings.save(dict(hotel_name=name, eur_to_inr=fx, low_risk_max=low, high_risk_min=high, window_months=win))
                        core.clear_data_cache()
                        st.session_state.pop("flt_range", None)
                        st.success("Settings saved.")
                        st.rerun()

    with t2:
        users = auth.load_users()
        with ui.card("st_users"):
            ui.card_title("Accounts")
            ui.table(pd.DataFrame([{"Username": u, "Name": v["name"], "E-mail": v["email"], "Role": v["role"]} for u, v in users.items()]))
        c1, c2 = st.columns(2)
        with c1, ui.card("st_adduser"):
            ui.card_title("Add user")
            with st.form("st_add_user", clear_on_submit=True):
                un = st.text_input("Username")
                nm = st.text_input("Full name")
                em = st.text_input("E-mail")
                rl = st.selectbox("Role", ["User", "Administrator"])
                pw = st.text_input("Password", type="password")
                if ui.stretch(st.form_submit_button, "Create user", type="primary"):
                    ok, msg = auth.add_user(un, nm, em, rl, pw)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
        with c2, ui.card("st_manage"):
            ui.card_title("Manage user")
            sel = st.selectbox("Account", list(users), key="st_sel")
            npw = st.text_input("New password", type="password", key="st_newpw")
            if st.button("Change password", key="st_chpw"):
                if len(npw) >= 6 and auth.set_password(sel, npw):
                    st.success("Password changed.")
                else:
                    st.error("Password must be at least 6 characters.")
            if st.button("Delete account", key="st_del"):
                if sel == st.session_state["auth"]["username"]:
                    st.error("You cannot delete the account you are logged in with.")
                else:
                    ok, msg = auth.delete_user(sel)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    with t3:
        from views import admin_analytics
        admin_analytics.model_panel("st_ml")

    with t4:
        with ui.card("st_maint"):
            ui.card_title("Maintenance")
            added = data_loader.read_added()
            st.write(f"Bookings added in the app: **{len(added)}**")
            c = st.columns(3)
            if c[0].button("Clear data cache", key="st_cache"):
                core.clear_data_cache()
                st.success("Cache cleared.")
            if c[1].button("Delete all added bookings", key="st_clear_added"):
                if config.ADDED_CSV.exists():
                    config.ADDED_CSV.unlink()
                core.clear_data_cache()
                st.success("Added bookings removed.")
                st.rerun()
            if c[2].button("Reset settings to defaults", key="st_reset"):
                settings.save(config.DEFAULT_SETTINGS)
                core.clear_data_cache()
                st.rerun()
