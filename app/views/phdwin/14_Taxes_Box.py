import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Taxes per BOE")
st.caption("Volume-weighted tax per BOE = Σ tax ÷ Σ Net Equivalent (Boe) per month.")
eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

dcol = "Prod Date" if "Prod Date" in e.columns else "EcoDate"
specs = [
    ("Total Sev Tax ($)", "Net Equivalent (Boe)", "Sev. Tax / BOE"),
    ("Total Ad Val Tax ($)", "Net Equivalent (Boe)", "Ad Val Tax / BOE"),
]
for num, den, title in specs:
    if num in e.columns and den in e.columns:
        charts.weighted_line(e, dcol, num, den, title=title)
