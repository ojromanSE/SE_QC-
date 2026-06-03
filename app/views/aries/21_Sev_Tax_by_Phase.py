import streamlit as st
from lib import charts, aries as A

st.title("Aries · Sev Tax by Phase")
st.caption("Volume-weighted severance tax per unit = Σ tax ÷ Σ volume per month (one general line per phase).")
mon = A.monthly_guard(st)
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)

specs = [
    ("Oil Sev Tax ($)", "Net Oil (Bbl)", "Sev Tax $/Bbl (Oil)"),
    ("Gas Sev Tax ($)", "Net Gas (Mcf)", "Sev Tax $/Mcf (Gas)"),
    ("NGL Sev Tax ($)", "Net NGL (Bbl)", "Sev Tax $/Bbl (NGL)"),
]
for num, den, title in specs:
    if num in e.columns and den in e.columns:
        charts.weighted_line(e, "Prod Date", num, den, title=title)
