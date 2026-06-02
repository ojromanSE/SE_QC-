import streamlit as st
from lib import charts, aries as A

st.title("Aries · Taxes Box Plot")
mon = A.monthly_guard(st)
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
for col, label in [("Sev. Tax/BOE", "Sev. Tax/BOE by Year"), ("Ad Val Tax/BOE", "Ad Val Tax/BOE by Year")]:
    if col in e.columns and "Year" in e.columns:
        charts.box_by_group(e, "Year", col, sample="LSE_NAME", title=label)
