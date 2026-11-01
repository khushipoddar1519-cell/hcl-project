"""Reusable UI building blocks (Streamlit)."""
import functools
import inspect

import pandas as pd
import streamlit as st

from . import analytics, config, settings

# ----------------------------------------------------------------------------- version-safe "stretch"
def _ver():
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (1, 0)


def stretch(fn, *args, **kwargs):
    """Call a Streamlit widget so that it fills the container on old and new Streamlit versions."""
    if _ver() >= (1, 50):
        try:
            return fn(*args, width="stretch", **kwargs)
        except TypeError:
            pass
    return fn(*args, use_container_width=True, **kwargs)


def plot(fig, key: str):
    stretch(st.plotly_chart, fig, key=key, config={"displayModeBar": False})


def table(df, key=None, **kw):
    stretch(st.dataframe, df, hide_index=True, **kw)


# ----------------------------------------------------------------------------- icons
_ICONS = {
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "xcircle": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M8 17v-6M13 17V6M18 17v-9"/>',
    "trend": '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
    "arrowup": '<path d="M12 19V5M5 12l7-7 7 7"/>',
    "bulb": '<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M17 4a4 4 0 0 1 0 8M22 21a7 7 0 0 0-4-6"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/>',
    "wallet": '<path d="M3 7a2 2 0 0 1 2-2h13v4"/><path d="M3 7v11a2 2 0 0 0 2 2h15V9H5a2 2 0 0 1-2-2z"/><circle cx="16.5" cy="14.5" r="1"/>',
    "bed": '<path d="M3 20V6M3 14h18v6M21 14v-2a3 3 0 0 0-3-3h-7v5"/><circle cx="7" cy="11" r="2"/>',
}


def icon(name, size=22, color="currentColor"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{_ICONS[name]}</svg>')


LOGO_SVG = """<svg class="logo" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
<rect x="10" y="6" width="44" height="46" rx="5" fill="#12a094"/>
<rect x="16" y="12" width="7" height="7" rx="1" fill="#d8fff9"/><rect x="28.5" y="12" width="7" height="7" rx="1" fill="#d8fff9"/><rect x="41" y="12" width="7" height="7" rx="1" fill="#d8fff9"/>
<rect x="16" y="23" width="7" height="7" rx="1" fill="#d8fff9"/><rect x="28.5" y="23" width="7" height="7" rx="1" fill="#d8fff9"/><rect x="41" y="23" width="7" height="7" rx="1" fill="#d8fff9"/>
<rect x="16" y="34" width="32" height="12" rx="2" fill="#0b6f68"/><rect x="19" y="37" width="9" height="5" rx="1.5" fill="#d8fff9"/><rect x="31" y="38.5" width="14" height="2.5" rx="1" fill="#d8fff9"/>
<rect x="6" y="52" width="52" height="6" rx="3" fill="#0b6f68"/></svg>"""


# ----------------------------------------------------------------------------- navigation
def goto(page: str):
    st.session_state["page"] = page


def go_button(label, page, key, icon_name=None, **kw):
    return stretch(st.button, label, key=key, on_click=goto, args=(page,),
                   icon=icon_name, **kw)


# ----------------------------------------------------------------------------- KPI / cards
def delta_html(p, good="up", label="vs. last year"):
    if p is None:
        return f'<div class="dl"><span>No prior-period data</span></div>'
    up = p >= 0
    arrow = "↑" if up else "↓"
    positive = (up and good == "up") or ((not up) and good == "down")
    cls = "up" if positive else "down"
    return f'<div class="dl {cls}">{arrow} {abs(p):.1f}% <span>{label}</span></div>'


def kpi_card(label, value, delta=None, tone="blue", icon_name="calendar", small=False, tooltip=""):
    title = f' title="{tooltip}"' if tooltip else ""
    html = (f'<div class="kpi t-{tone} {"sm" if small else ""}"{title}><div class="ic">{icon(icon_name)}</div>'
            f'<div class="lb">{label}</div><div class="vl">{value}</div>{delta or ""}</div>')
    st.markdown(html, unsafe_allow_html=True)


def card(key):
    return st.container(key=f"card_{key}")


def card_title(text, sub=None):
    st.markdown(f'<div class="card-title">{text}</div>' + (f'<div class="card-sub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)


def page_header(title, sub=None):
    st.markdown(f'<div class="page-title">{title}</div>' + (f'<div class="page-sub">{sub}</div>' if sub else ""),
                unsafe_allow_html=True)


def html_table(df: pd.DataFrame, formats: dict | None = None, num_cols=()):
    formats = formats or {}
    head = "".join(f'<th class="{"num" if c in num_cols else ""}">{c}</th>' for c in df.columns)
    body = ""
    for _, r in df.iterrows():
        tds = ""
        for c in df.columns:
            v = formats[c](r[c]) if c in formats else r[c]
            tds += f'<td class="{"num" if c in num_cols else ""}">{v}</td>'
        body += f"<tr>{tds}</tr>"
    st.markdown(f'<table class="ht"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>',
                unsafe_allow_html=True)


# ----------------------------------------------------------------------------- plotly styling
def style_fig(fig, height=340):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=30, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#27424a"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#cfe3e1")
    fig.update_yaxes(gridcolor="rgba(120,160,160,.22)", zeroline=False)
    return fig


# ----------------------------------------------------------------------------- filter bar
def _sync_range(prefix):
    val = st.session_state.get(f"{prefix}_range")
    if isinstance(val, (list, tuple)) and len(val) == 2:
        st.session_state["flt_range"] = (val[0], val[1])


def _sync_hotel(prefix):
    st.session_state["flt_hotel"] = st.session_state.get(f"{prefix}_hotel", "All")


def _reset_range(prefix):
    st.session_state.pop("flt_range", None)
    st.session_state.pop(f"{prefix}_range", None)


def filter_bar(df_all: pd.DataFrame, prefix: str, hotel: bool = True, inline: bool = False, label="Period"):
    """Period (+ hotel) filter shared by all pages. Returns a context dict."""
    cfg = settings.load()
    dmin, dmax = df_all["arrival_date"].min().date(), df_all["arrival_date"].max().date()
    if "flt_range" not in st.session_state:
        st.session_state["flt_range"] = analytics.default_window(df_all, int(cfg["window_months"]))
    s, e = st.session_state["flt_range"]
    s, e = max(min(s, dmax), dmin), max(min(e, dmax), dmin)
    st.session_state.setdefault("flt_hotel", "All")

    if inline:
        c1 = c2 = c3 = st.container()
    else:
        cols = st.columns([3, 2, 1, 4]) if hotel else st.columns([3, 1, 6])
        c1 = cols[0]
        c2 = cols[1] if hotel else None
        c3 = cols[2] if hotel else cols[1]
    with c1:
        val = st.date_input(label, value=(s, e), min_value=dmin, max_value=dmax, key=f"{prefix}_range",
                            on_change=_sync_range, args=(prefix,), format="DD/MM/YYYY")
    if isinstance(val, (list, tuple)) and len(val) == 2:
        s, e = val
    if hotel:
        opts = ["All"] + sorted(df_all["hotel"].unique().tolist())
        cur = st.session_state["flt_hotel"] if st.session_state["flt_hotel"] in opts else "All"
        with c2:
            h = st.selectbox("Hotel", opts, index=opts.index(cur), key=f"{prefix}_hotel",
                             on_change=_sync_hotel, args=(prefix,))
    else:
        h = "All"
    if not inline:
        with c3:
            st.write("")
            st.button("↺ Reset", key=f"{prefix}_reset", on_click=_reset_range, args=(prefix,),
                      help="Reset to the default period")
    base = df_all if h == "All" else df_all[df_all["hotel"] == h]
    df = analytics.slice_window(base, s, e)
    return {"all": df_all, "base": base, "df": df, "start": pd.Timestamp(s), "end": pd.Timestamp(e), "hotel": h}


def empty_guard(ctx) -> bool:
    if ctx["df"].empty:
        st.warning("No bookings in the selected period / hotel. Widen the period filter.")
        return True
    return False
