import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Sev Tax by Phase")
st.caption("Volume-weighted severance tax per unit = Σ tax ÷ Σ volume per month (one general line per phase).")
eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

dcol = "Prod Date" if "Prod Date" in e.columns else "EcoDate"
specs = [
    ("Sev Tax Oil ($)", "Net Oil (Bbl)", "Sev Tax $/Bbl (Oil)"),
    ("Sev Tax Gas ($)", "Net Gas (Mcf)", "Sev Tax $/Mcf (Gas)"),
    ("Sev Tax NGL ($)", "Net NGL (Bbl)", "Sev Tax $/Bbl (NGL)"),
]
for num, den, title in specs:
    if num in e.columns and den in e.columns:
        charts.weighted_line(e, dcol, num, den, title=title)
