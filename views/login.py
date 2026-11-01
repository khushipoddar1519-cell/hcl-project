"""Login screen."""
import streamlit as st

from modules import auth, components as ui, config, settings


def _do_login(username, user, remember=False):
    st.session_state["auth"] = user
    st.session_state["page"] = "dashboard" if user["role"] == "Administrator" else "home"
    settings.set_remembered(username if remember else None)
    st.rerun()


def render():
    _, mid, _ = st.columns([1.1, 1, 1.1])
    with mid:
        with st.container(key="card_login"):
            st.markdown(
                f'<div class="login-wrap">{ui.LOGO_SVG}<div class="login-title">{config.APP_NAME}</div>'
                f'<div class="login-sub">Cancellation &amp; Revenue<br>Management</div>'
                f'<div class="login-hr"></div>'
                f'<div class="login-hint">Sign in to access your<br>dashboard and insights</div></div>',
                unsafe_allow_html=True)
            tab_login, tab_signup = st.tabs(["🔑 Sign In", "✨ Create Account"])

            with tab_login:
                with st.form("login_form", clear_on_submit=False):
                    ident = st.text_input("Email or Username", placeholder="Email or Username")
                    pwd = st.text_input("Password", type="password", placeholder="Password")
                    submit = ui.stretch(st.form_submit_button, "Sign In", type="primary")
                if submit:
                    res = auth.authenticate(ident, pwd)
                    if res:
                        _do_login(res[0], res[1], remember=False)
                    else:
                        st.error("Invalid username / email or password.")

                with st.popover("Forgot password?"):
                    st.caption("Enter your username / email, the recovery key and your new password.")
                    f_id = st.text_input("Username / email", key="fp_id")
                    f_key = st.text_input("Recovery key", key="fp_key", type="password")
                    f_new = st.text_input("New password", key="fp_new", type="password")
                    if st.button("Reset password", key="fp_btn"):
                        ok, msg = auth.reset_password(f_id, f_key, f_new)
                        (st.success if ok else st.error)(msg)

            with tab_signup:
                st.caption("Create your hotel analytics account.")
                with st.form("signup_form", clear_on_submit=False):
                    su_name = st.text_input("Full Name", placeholder="e.g. John Doe")
                    su_email = st.text_input("Email", placeholder="e.g. john@hotel.com")
                    su_user = st.text_input("Username", placeholder="e.g. jdoe")
                    su_role = st.selectbox("Role", ["User", "Administrator"])
                    su_pwd = st.text_input("Password (min 4 chars)", type="password", placeholder="Password")
                    su_submit = ui.stretch(st.form_submit_button, "Create Account & Sign In", type="primary")

                if su_submit:
                    if not su_user or not su_pwd or not su_email:
                        st.error("All fields are required.")
                    elif len(su_pwd) < 4:
                        st.error("Password must be at least 4 characters.")
                    else:
                        ok, msg = auth.add_user(su_user, su_name or su_user.title(), su_email, su_role, su_pwd)
                        if ok:
                            res = auth.authenticate(su_user, su_pwd)
                            if res:
                                st.success("Account created! Logging in...")
                                _do_login(res[0], res[1], remember=False)
                        else:
                            st.error(msg)
            st.markdown('<div class="login-foot">Better Insights &nbsp;•&nbsp; Smarter Decisions &nbsp;•&nbsp; Higher Revenue</div>',
                        unsafe_allow_html=True)
