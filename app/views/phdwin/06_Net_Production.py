import streamlit as st
import pandas as pd
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Net Production")

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
    df = pd.concat(pieces, ignore_index=True).groupby("Prod Date", dropna=False).sum(numeric_only=True).reset_index()
    charts.grouped_column(df, "Prod Date", [c for c in ["Historical", "Forecast"] if c in df.columns],
                          title=label, series_colors=charts.production_tones(label))

combo("Net Oil (Bbl/d)", "Net Historical Oil (Bbl/d)", "Net Oil (Bbl/d)")
combo("Net Gas (Mcf/d)", "Net Historical Gas Sold (Mcf/d)", "Net Gas (Mcf/d)")
combo("Net NGL (Bbl/d)", "Net Historical NGL (Bbl/d)", "Net NGL (Bbl/d)")
combo("Net Equivalent (Boe/d)", "Net Historical Equivalent (Boe/d)", "Net Equivalent (Boe/d)")
