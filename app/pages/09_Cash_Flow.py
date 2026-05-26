import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Cash Flow")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

work = e.copy()
for src, neg in [("Total Opex ($)", "Total Opex ($) neg"),
                 ("Total Sev Tax ($)", "Total Sev Tax ($) neg"),
                 ("Total Investment ($)", "Total Investment ($) neg")]:
    if neg not in work.columns and src in work.columns:
        work[neg] = -work[src]

bars = [c for c in ["Total Revenue ($)", "Total Opex ($) neg", "Total Sev Tax ($) neg",
                    "Total Ad Val Tax ($)", "Total Investment ($) neg"] if c in work.columns]
line = "BFIT CF ($)" if "BFIT CF ($)" in work.columns else ""
if "Year" not in work.columns:
    st.error("Need Year (derived from Prod Date)."); st.stop()
charts.combo_revenue_opex_cf(work, "Year", bars, line, title="Cash Flow Components & BFIT CF by Year")
