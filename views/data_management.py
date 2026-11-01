"""Admin – Data Management."""
import shutil
from datetime import datetime

import pandas as pd
import streamlit as st

from modules import analytics as an, components as ui, config, core, data_loader


def render(user):
    df_all = core.data()
    ui.page_header("Data Management", "Browse, edit, upload and quality-check the booking data.")
    t1, t2, t3, t4 = st.tabs(["🗃 Dataset explorer", "✏️ Added bookings", "⬆ Upload / replace dataset", "🩺 Data quality"])

    with t1:
        with ui.card("dm_explore"):
            c = st.columns(4)
            hotel = c[0].multiselect("Hotel", sorted(df_all["hotel"].unique()), key="dm_hotel")
            seg = c[1].multiselect("Market segment", sorted(df_all["segment"].unique()), key="dm_seg")
            status = c[2].multiselect("Reservation status", sorted(df_all["reservation_status"].unique()), key="dm_status")
            year = c[3].multiselect("Arrival year", sorted(df_all["arrival_date_year"].unique()), key="dm_year")
            d = df_all
            if hotel: d = d[d["hotel"].isin(hotel)]
            if seg: d = d[d["segment"].isin(seg)]
            if status: d = d[d["reservation_status"].isin(status)]
            if year: d = d[d["arrival_date_year"].isin(year)]
            st.caption(f"{len(d):,} of {len(df_all):,} rows match.")
            cols_default = ["hotel", "is_canceled", "lead_time", "arrival_date", "total_nights", "adults", "children", "segment",
                            "distribution_channel", "room_group", "deposit_type", "customer_type", "adr", "revenue", "reservation_status", "source"]
            cols = st.multiselect("Columns", list(df_all.columns), default=cols_default, key="dm_cols")
            ui.table(d[cols].head(1000), column_config={"revenue": st.column_config.NumberColumn("Revenue (₹)", format="₹ %.0f")})
            st.caption("Showing the first 1,000 matching rows.")
            if st.checkbox("Prepare CSV download of all matching rows", key="dm_prep"):
                st.download_button("⬇ Download CSV", d[cols].to_csv(index=False).encode(), "bookings_filtered.csv", "text/csv", key="dm_dl")

    with t2:
        added = data_loader.read_added()
        with ui.card("dm_added"):
            ui.card_title("Bookings created in the app", "Update the outcome of a booking (e.g. Canceled / Check-Out) – it feeds the dashboards and the next model training.")
            if added.empty:
                st.info("No bookings have been added yet. Use **Add Booking & Risk** to create one.")
            else:
                show = added[["booking_id", "guest_name", "hotel", "arrival_date_year", "arrival_date_month", "arrival_date_day_of_month",
                              "lead_time", "adr", "market_segment", "risk_score", "risk_level", "reservation_status", "created_by", "created_at"]]
                edited = st.data_editor(
                    show, key="dm_editor", num_rows="dynamic",
                    disabled=[c for c in show.columns if c not in ("guest_name", "reservation_status", "adr")],
                    column_config={"reservation_status": st.column_config.SelectboxColumn("Status", options=["Confirmed", "Check-Out", "Canceled", "No-Show"]),
                                   "adr": st.column_config.NumberColumn("ADR (€)", format="%.2f")},
                    **({"width": "stretch"} if ui._ver() >= (1, 50) else {"use_container_width": True}))
                if st.button("💾 Save changes", key="dm_save", type="primary"):
                    keep = added[added["booking_id"].isin(edited["booking_id"])].copy().set_index("booking_id")
                    ed = edited.set_index("booking_id")
                    for col in ("guest_name", "reservation_status", "adr"):
                        keep[col] = ed[col]
                    keep["is_canceled"] = (keep["reservation_status"] == "Canceled").astype(int)
                    data_loader.write_added(keep.reset_index())
                    core.clear_data_cache()
                    st.success("Changes saved.")
                    st.rerun()

    with t3:
        with ui.card("dm_upload"):
            ui.card_title("Replace the base dataset", "Upload a CSV / XLSX with the same 32 columns as the original hotel-bookings file. A backup of the current file is kept.")
            up = st.file_uploader("Choose a file", type=["csv", "xlsx"], key="dm_file")
            if up is not None:
                try:
                    new = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
                except Exception as e:
                    st.error(f"Could not read the file: {e}")
                    new = None
                if new is not None:
                    missing = data_loader.validate_upload(new)
                    if missing:
                        st.error(f"Missing required columns: {', '.join(missing)}")
                    else:
                        st.success(f"Valid file: {len(new):,} rows × {len(new.columns)} columns.")
                        ui.table(new.head(10))
                        if st.button("Replace dataset", key="dm_replace", type="primary"):
                            backup = config.DATA_DIR / f"hotel_bookings_backup_{datetime.now():%Y%m%d_%H%M%S}.csv"
                            shutil.copy(config.BASE_CSV, backup)
                            if "reservation_status_date" in new.columns:
                                new["reservation_status_date"] = pd.to_datetime(new["reservation_status_date"], errors="coerce").dt.strftime("%Y-%m-%d")
                            new[data_loader.BASE_COLUMNS].to_csv(config.BASE_CSV, index=False)
                            core.clear_data_cache()
                            st.success(f"Dataset replaced (backup: {backup.name}). Retrain the model from Settings → Model.")
                            st.rerun()

    with t4:
        base = df_all[df_all["source"] == "dataset"]
        k = st.columns(4)
        k[0].metric("Rows", f"{len(base):,}")
        k[1].metric("Columns", len(data_loader.BASE_COLUMNS))
        k[2].metric("Duplicate rows", f"{int(base[data_loader.BASE_COLUMNS[:-1]].duplicated().sum()):,}")
        k[3].metric("Date span", f"{base['arrival_date'].min():%b %Y} – {base['arrival_date'].max():%b %Y}")
        raw = data_loader.read_base()
        with ui.card("dm_missing"):
            ui.card_title("Missing values (raw file)")
            miss = raw.isna().sum().reset_index()
            miss.columns = ["Column", "Missing"]
            miss["% missing"] = (miss["Missing"] / len(raw) * 100).round(2)
            ui.table(miss[miss["Missing"] > 0].sort_values("Missing", ascending=False))
        with ui.card("dm_outliers"):
            ui.card_title("Checks & cleaning rules applied")
            checks = pd.DataFrame([
                ("ADR < 0 or > 1000 €", int(((raw["adr"] < 0) | (raw["adr"] > 1000)).sum()), "Clipped to [0, 1000]"),
                ("Bookings with zero guests", int(((raw["adults"] + raw["children"].fillna(0) + raw["babies"]) == 0).sum()), "Kept (flagged only)"),
                ("Bookings with zero nights", int(((raw["stays_in_weekend_nights"] + raw["stays_in_week_nights"]) == 0).sum()), "Kept – revenue = 0"),
                ("Missing children", int(raw["children"].isna().sum()), "Filled with 0"),
                ("Missing country", int(raw["country"].isna().sum()), "Labelled 'Unknown'"),
            ], columns=["Check", "Rows affected", "Treatment"])
            ui.table(checks)
