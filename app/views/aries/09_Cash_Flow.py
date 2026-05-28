import streamlit as st
from lib import charts, aries as A

st.title("Aries · Cash Flow")
mon = A.get_monthly()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
bars = [c for c in ["Total Revenue ($)", "Total Opex ($) neg", "Total Sev Tax ($) neg",
                    "Total Ad Val Tax ($) neg", "Total Investment ($) neg"] if c in e.columns]
if "Year" not in e.columns:
    st.error("Need Year."); st.stop()
charts.combo_revenue_opex_cf(e, "Year", bars, "BFIT CF ($)", "Cash Flow Components & BFIT CF by Year")
