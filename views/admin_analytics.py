"""Admin – Analytics hub (all analyses + ML model diagnostics)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import analytics as an, components as ui, config, core, model
from views import cancellation, forecasting, revenue, segments


def model_panel(key="ml"):
    bundle = core.get_model()
    m = bundle["metrics"]
    k = st.columns(5)
    for col, (lbl, val) in zip(k, [("Accuracy", m["accuracy"]), ("Precision", m["precision"]), ("Recall", m["recall"]),
                                  ("F1 score", m["f1"]), ("ROC-AUC", m["auc"])]):
        col.metric(lbl, f"{val * 100:.1f}%" if lbl != "ROC-AUC" else f"{val:.3f}")
    st.caption(f"Trained {bundle['trained_at']} on {bundle['n_rows']:,} completed reservations · evaluated on {m['test_rows']:,} unseen rows · base cancellation rate {m['base_rate'] * 100:.1f}%.")
    c1, c2 = st.columns(2)
    with c1, ui.card(f"{key}_imp"):
        ui.card_title("What the model relies on", "Permutation importance (drop in ROC-AUC when a feature is shuffled).")
        imp = bundle["importance"].head(12).copy()
        imp["feature"] = imp["feature"].map(lambda f: model.FRIENDLY.get(f, f))
        fig = px.bar(imp.iloc[::-1], x="importance", y="feature", orientation="h", color="importance", color_continuous_scale="Tealgrn")
        fig.update_coloraxes(showscale=False)
        ui.plot(ui.style_fig(fig, 380), f"{key}_imp_fig")
    with c2, ui.card(f"{key}_cm"):
        ui.card_title("Confusion matrix (hold-out set)")
        cm = m["confusion"]
        fig = go.Figure(go.Heatmap(z=cm, x=["Predicted kept", "Predicted cancelled"], y=["Actually kept", "Actually cancelled"],
                                   colorscale="Tealgrn", text=cm, texttemplate="%{text:,}", showscale=False))
        fig.update_yaxes(autorange="reversed")
        ui.plot(ui.style_fig(fig, 380), f"{key}_cm_fig")
    if st.button("🔄 Retrain model on current data", key=f"{key}_retrain", type="primary"):
        with st.spinner("Training… this takes about 20–40 seconds"):
            core.retrain()
        st.success("Model retrained.")
        st.rerun()


def render(user):
    df_all = core.data()
    ui.page_header("Analytics", "Deep-dive analyses and model diagnostics in one place.")
    ctx = ui.filter_bar(df_all, "ax")
    if ui.empty_guard(ctx):
        return
    t = st.tabs(["🚫 Cancellations", "📈 Demand forecast", "💰 Revenue", "🛏 Rooms & segments", "🤖 ML model"])
    with t[0]:
        cancellation.body(ctx, key="ax_cx")
    with t[1]:
        forecasting.body(ctx, key="ax_fc")
    with t[2]:
        revenue.body(ctx, key="ax_rv")
    with t[3]:
        segments.body(ctx, key="ax_sg")
    with t[4]:
        model_panel("ax_ml")
