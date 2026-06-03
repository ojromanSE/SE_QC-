import streamlit as st
from lib import charts, aries as A

st.title("Aries · Taxes per BOE")
st.caption("Volume-weighted tax per BOE = Σ tax ÷ Σ Net Equivalent (Boe) per month.")
mon = A.monthly_guard(st)
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)

specs = [
    ("Total Sev Tax ($)", "Net Equivalent (Boe)", "Sev. Tax / BOE"),
    ("Total Ad Val Tax ($)", "Net Equivalent (Boe)", "Ad Val Tax / BOE"),
]
for num, den, title in specs:
    if num in e.columns and den in e.columns:
        charts.weighted_line(e, "Prod Date", num, den, title=title)
