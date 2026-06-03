import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Opex ($/Boe) vs Time")
st.caption("Volume-weighted Opex per BOE = Σ Total Opex ($) ÷ Σ Net Equivalent (Boe) per month.")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

dcol = "Prod Date" if "Prod Date" in e.columns else "EcoDate"
c1, c2 = st.columns([2, 1])
with c1:
    if {"Total Opex ($)", "Net Equivalent (Boe)"}.issubset(e.columns):
        charts.weighted_line(e, dcol, "Total Opex ($)", "Net Equivalent (Boe)",
                             title="Opex ($/Boe) vs Time")
    elif "Opex ($/Boe)" in e.columns:
        # Fallback if revenue+volume cols are absent.
        charts.line(e, dcol, "Opex ($/Boe)", title="Opex ($/Boe) vs Time")
with c2:
    if "Opex ($/Boe)" in e.columns:
        charts.histogram(e, "Opex ($/Boe)", title="Opex ($/Boe) distribution")
