import streamlit as st
from lib import charts, aries as A

st.title("Aries · Net Cash Flow by Case")
mon = A.get_monthly()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
if "LSE_NAME" in e.columns:
    if "BFIT CF ($)" in e.columns:
        charts.line(e, "Prod Date", "BFIT CF ($)", color="LSE_NAME", title="BFIT CF ($) by LEASE_NAME")
    if "Total Opex ($)" in e.columns:
        charts.line(e, "Prod Date", "Total Opex ($)", color="LSE_NAME", title="Total Opex ($) by LEASE_NAME")
