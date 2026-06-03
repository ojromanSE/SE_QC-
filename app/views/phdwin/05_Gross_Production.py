import streamlit as st
import pandas as pd
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Gross Production")

eco = model.get_lse_eco()
mon = model.get_mon_info()
if eco is None and mon is None:
    st.warning("Load PHDWin first."); st.stop()

sel = st.session_state.get("rsvcat_selection") or []

def combo(label, hist_col, forecast_col):
    pieces = []
    if mon is not None and hist_col in mon.columns:
        m = apply_rsvcat(mon, sel, model.get_lse_info())[["Prod Date", hist_col]].rename(columns={hist_col: "Historical"})
        pieces.append(m)
    if eco is not None and forecast_col in eco.columns:
        e = apply_rsvcat(eco, sel)[["Prod Date", forecast_col]].rename(columns={forecast_col: "Forecast"})
        pieces.append(e)
    if not pieces:
        st.info(f"No data for {label}."); return
    df = pd.concat(pieces, ignore_index=True)
    df = df.groupby("Prod Date", dropna=False).sum(numeric_only=True).reset_index()
    charts.grouped_column(df, "Prod Date", [c for c in ["Historical", "Forecast"] if c in df.columns],
                          title=label, series_colors=charts.production_tones(label))

combo("Gross Oil (Bbl/d)", "Historical Oil Gross from Product (Bbl/d)", "Gross Oil (Bbl/d)")
combo("Gross Gas (Mcf/d)", "Historical Gas Gross from Product (Mscf/d)", "Gross Gas (Mcf/d)")
combo("Gross NGL (Bbl/d)", "Historical NGL Gross from Product (Bbl/d)", "Gross NGL (Bbl/d)")
combo("Gross Equivalent (Boe/d)", "Historical Equivalent Gross from Product (Boe/d)", "Gross Equivalent (Boe/d)")
