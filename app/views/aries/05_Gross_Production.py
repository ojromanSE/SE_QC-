import streamlit as st
import pandas as pd
from lib import charts, aries as A

st.title("Aries · Gross Production")
mon = A.get_monthly(); prod = A.get_product()
if mon is None and prod is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY / AC_PRODUCT)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []

def combo(label, hist_col, fc_col):
    pieces = []
    if prod is not None and hist_col in prod.columns:
        p = A.apply_rsvcat(prod, sel)[["Prod Date", hist_col]].rename(columns={hist_col: "Historical"})
        pieces.append(p)
    if mon is not None and fc_col in mon.columns:
        m = A.apply_rsvcat(mon, sel)[["Prod Date", fc_col]].rename(columns={fc_col: "Forecast"})
        pieces.append(m)
    if not pieces:
        st.info(f"No data for {label}."); return
    df = pd.concat(pieces, ignore_index=True).groupby("Prod Date", dropna=False).sum(numeric_only=True).reset_index()
    charts.grouped_column(df, "Prod Date", [c for c in ["Historical", "Forecast"] if c in df.columns],
                          title=label, series_colors=charts.production_tones(label))

combo("Gross Oil (Bbl/d)", "Historical Oil Gross from Product (Bbl/d)", "Gross Oil (Bbl/d)")
combo("Gross Gas (Mcf/d)", "Historical Gas Gross from Product (Bbl/d)", "Gross Gas (Mcf/d)")
combo("Gross Water (Bbl/d)", "Historical Water Gross from Product (bbl/d)", "Gross Water (Bbl/d)")
combo("Gross Equivalent (Boe/d)", "Historical Equivalent Gross from Product (Bbl/d)", "Gross Equivalent (Boe/d)")
