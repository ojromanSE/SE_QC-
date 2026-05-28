import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Realized Prices")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

dcol = "EcoDate" if "EcoDate" in e.columns else "Prod Date"
if "Realized Oil Price ($/Bbl)" in e.columns:
    charts.line(e, dcol, "Realized Oil Price ($/Bbl)", color="LSE_NAME", title="Realized Oil Price ($/Bbl)")
if "Realized Gas Price ($/Mcf)" in e.columns:
    charts.line(e, dcol, "Realized Gas Price ($/Mcf)", color="LSE_NAME", title="Realized Gas Price ($/Mcf)")
