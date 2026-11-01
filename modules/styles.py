"""Global CSS – glassmorphism teal theme that mirrors the reference design."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, [class*="st-"], button, input, textarea { font-family: 'Inter', sans-serif; }
.stApp {
  background:
    radial-gradient(circle at 8% 0%, rgba(120,225,210,.55) 0%, transparent 42%),
    radial-gradient(circle at 95% 8%, rgba(150,205,255,.45) 0%, transparent 38%),
    radial-gradient(circle at 60% 100%, rgba(140,230,215,.45) 0%, transparent 45%),
    linear-gradient(135deg, #e9f9f6 0%, #d9f2ef 50%, #e8f4fb 100%);
  background-attachment: fixed;
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
.block-container { padding-top: 1.1rem; padding-bottom: 2.5rem; max-width: 1450px; }
h1, h2, h3 { color: #0e2f35; letter-spacing: -.01em; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
  background: rgba(255,255,255,.55); backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255,255,255,.8);
}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarContent"] { padding-top: 1rem; }
[data-testid="stSidebar"] [data-testid^="stBaseButton"] {
  justify-content: flex-start; border: none !important; background: transparent !important;
  color: #1d3b44 !important; box-shadow: none !important; border-radius: 14px !important;
  padding: .62rem .9rem !important; font-weight: 500 !important; text-align: left;
}
[data-testid="stSidebar"] [data-testid^="stBaseButton"]:hover { background: rgba(94,214,198,.18) !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] button[kind="primary"] {
  background: rgba(94,214,198,.38) !important; color: #0a5a54 !important; font-weight: 700 !important;
}

/* ---------- glass cards (keyed containers: st.container(key="card_*")) ---------- */
[class*="st-key-card"] {
  background: rgba(255,255,255,.74); border: 1px solid rgba(255,255,255,.95);
  border-radius: 20px; padding: 1.15rem 1.35rem; box-shadow: 0 10px 30px rgba(18,120,120,.09);
  margin-bottom: .9rem;
}
[class*="st-key-card"] [class*="st-key-card"] { box-shadow: none; padding: .6rem; background: rgba(255,255,255,.55); }
.card-title { font-size: 1.12rem; font-weight: 700; color: #10333a; margin-bottom: .45rem; }
.card-sub { color: #5b7b80; font-size: .85rem; margin-top: -.25rem; margin-bottom: .6rem; }
.page-title { font-size: 1.9rem; font-weight: 800; color: #0e2f35; margin: .2rem 0 0 0; }
.page-sub { color: #476870; font-size: 1.02rem; margin-bottom: 1rem; }
.brand { display:flex; align-items:center; gap:.7rem; font-size:1.45rem; font-weight:800; color:#0e3a40; }
.brand svg { width: 42px; height: 42px; }

/* ---------- buttons ---------- */
[data-testid="stBaseButton-primary"], button[kind="primary"],
[data-testid="stBaseButton-primaryFormSubmit"], button[kind="primaryFormSubmit"] {
  background: linear-gradient(135deg,#19c1ad,#0b7f77) !important; color: #fff !important;
  border: none !important; border-radius: 13px !important; font-weight: 700 !important;
  padding: .55rem 1rem !important; box-shadow: 0 6px 16px rgba(15,157,146,.28) !important;
}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { filter: brightness(1.06); }
[data-testid="stBaseButton-secondary"], button[kind="secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stBaseButton-popover"] {
  background: rgba(255,255,255,.9) !important; color: #0e6f68 !important; border: 1.5px solid #6fd3c6 !important;
  border-radius: 13px !important; font-weight: 600 !important;
}
[data-testid="stBaseButton-secondary"]:hover { border-color:#0f9d92 !important; background:#f2fffd !important; }
[data-testid="stBaseButton-tertiary"] { color:#0f9d92 !important; font-weight:700 !important; }
[data-testid="stDownloadButton"] button { border-radius: 13px !important; }

/* quick action tiles */
[class*="st-key-quick"] [data-testid^="stBaseButton"] {
  width: 100%; justify-content: flex-start; padding: 1.05rem 1.1rem !important; border-radius: 16px !important;
  background: rgba(255,255,255,.88) !important; border: 1px solid rgba(255,255,255,1) !important;
  box-shadow: 0 6px 18px rgba(18,120,120,.08) !important; color: #123b42 !important; font-weight: 600 !important;
}
[class*="st-key-quick"] [data-testid^="stBaseButton"]:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(18,120,120,.14) !important; }

/* inputs */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"], .stDateInput > div > div {
  border-radius: 12px !important; background: rgba(255,255,255,.92) !important;
}
label, .stMarkdown p { color: #264a52; }
[data-testid="stForm"] { border: none; padding: 0; background: transparent; }
[data-testid="stTabs"] button[role="tab"] { font-weight: 600; }
[data-testid="stTabs"] [aria-selected="true"] { color:#0b7f77 !important; }
[data-testid="stExpander"] { background: rgba(255,255,255,.6); border-radius: 14px; border: 1px solid rgba(255,255,255,.9); }

/* ---------- KPI cards ---------- */
.kpi { border-radius: 18px; padding: 1rem 1.05rem; border: 1px solid rgba(255,255,255,.95);
       box-shadow: 0 8px 22px rgba(18,120,120,.08); height: 100%; min-height: 150px; }
.kpi.sm { min-height: 128px; padding: .85rem .95rem; }
.kpi .ic { width: 42px; height: 42px; border-radius: 50%; display:flex; align-items:center; justify-content:center;
           margin-bottom: .6rem; background: rgba(255,255,255,.85); }
.kpi .ic svg { width: 22px; height: 22px; }
.kpi .lb { font-size: .86rem; color: #3b5a61; font-weight: 500; }
.kpi .vl { font-size: 1.7rem; font-weight: 800; color: #0e2f35; line-height: 1.25; white-space: nowrap; }
.kpi.sm .vl { font-size: 1.45rem; }
.kpi .dl { font-size: .78rem; font-weight: 600; margin-top: .15rem; color:#6b8186; }
.kpi .dl.up { color: #14a36b; } .kpi .dl.down { color: #e5484d; }
.kpi .dl span { color:#7a8f94; font-weight: 500; }
.t-blue   { background: linear-gradient(160deg,#eef3ff,#e2eeff); } .t-blue .ic { color:#3b82f6; }
.t-green  { background: linear-gradient(160deg,#ecfbf4,#dcf6ea); } .t-green .ic { color:#12a466; }
.t-teal   { background: linear-gradient(160deg,#e9f8fb,#d7f1f7); } .t-teal .ic { color:#0e8fb0; }
.t-orange { background: linear-gradient(160deg,#fff6e8,#ffeacb); } .t-orange .ic { color:#f08c1a; }
.t-red    { background: linear-gradient(160deg,#fff0f0,#ffe0e2); } .t-red .ic { color:#e5484d; }
.t-purple { background: linear-gradient(160deg,#f3efff,#e7e0ff); } .t-purple .ic { color:#7c5cf0; }

/* ---------- insights ---------- */
.ins { display:flex; align-items:center; gap:.9rem; padding:.35rem 0; min-height: 58px; }
.ins .ci { width:46px; height:46px; border-radius:50%; flex:none; display:flex; align-items:center; justify-content:center; }
.ci svg { width:24px; height:24px; }
.ci.red { background:#ffe3e5; color:#e5484d; } .ci.green { background:#d9f7e8; color:#13a366; }
.ci.purple { background:#e9e2ff; color:#7c5cf0; } .ci.teal { background:#d6f2f6; color:#0e8fb0; }
.ins .tt { font-weight: 700; color:#10333a; font-size: 1.02rem; }
.ins .ds { color:#587479; font-size: .9rem; }
.tipbox { background: linear-gradient(90deg,#e3f1ff,#e9f6fb); border-radius: 16px; padding: .95rem 1.2rem;
          color:#25525c; border: 1px solid rgba(255,255,255,.95); display:flex; align-items:center; gap:.9rem; }
.tipbox b { color:#10333a; }

/* ---------- html table ---------- */
table.ht { width:100%; border-collapse: collapse; font-size:.9rem; }
table.ht th { text-align:left; padding:.5rem .6rem; color:#274a52; background: rgba(150,205,200,.22); font-weight:700; }
table.ht td { padding:.55rem .6rem; border-bottom: 1px solid rgba(120,160,160,.2); color:#1b3d44; }
table.ht td.num, table.ht th.num { text-align: right; }

/* risk badges */
.badge { display:inline-block; padding:.28rem .8rem; border-radius:999px; font-weight:700; font-size:.9rem; }
.badge.low { background:#d9f7e8; color:#0e8f58; } .badge.medium { background:#fff0d1; color:#b36b00; }
.badge.high { background:#ffe0e2; color:#d12f3a; }
.reco { padding:.55rem .8rem; border-left:4px solid #19c1ad; background:rgba(255,255,255,.7); border-radius:8px; margin:.35rem 0; color:#244a52; }

/* ---------- login ---------- */
.login-wrap { text-align:center; }
.login-wrap svg.logo { width: 92px; height: 92px; margin-bottom:.4rem; }
.login-title { font-size: 2.3rem; font-weight: 800; color:#0e3a40; line-height:1.1; }
.login-sub { font-size: 1.28rem; font-weight: 500; color:#0e3a40; margin:.35rem 0 1rem 0; line-height:1.3; }
.login-hr { height:1px; background: linear-gradient(90deg,transparent,#9ccfc8,transparent); margin: .6rem 0 1rem 0; }
.login-hint { color:#476870; font-size:1.05rem; margin-bottom: 1rem; }
.login-foot { text-align:center; color:#476870; font-size:.78rem; margin-top: 1.2rem; }
.or-line { text-align:center; color:#587479; font-size:.85rem; margin:.25rem 0 .4rem 0; }
.waves { position: fixed; left:0; right:0; bottom:0; height: 180px; pointer-events:none; z-index:0; opacity:.55; }
</style>
"""

HIDE_SIDEBAR = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display:none !important; }
</style>
"""

WAVES = """
<svg class="waves" viewBox="0 0 1440 200" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
<path d="M0,120 C240,40 480,200 760,120 C1000,50 1200,60 1440,130 L1440,200 L0,200Z" fill="#8fe3d6" opacity=".55"/>
<path d="M0,150 C300,90 520,210 820,150 C1080,100 1260,120 1440,160 L1440,200 L0,200Z" fill="#6fd0c8" opacity=".5"/>
</svg>
"""


def inject(hide_sidebar: bool = False):
    st.markdown(CSS, unsafe_allow_html=True)
    if hide_sidebar:
        st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)
        st.markdown(WAVES, unsafe_allow_html=True)
