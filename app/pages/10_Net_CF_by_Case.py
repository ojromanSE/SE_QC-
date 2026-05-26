import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Net Cash Flow by Case")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

if "LSE_NAME" in e.columns:
    if "BFIT CF ($)" in e.columns:
        charts.line(e, "Prod Date", "BFIT CF ($)", color="LSE_NAME", title="BFIT CF ($) by LSE_NAME")
    if "Total Opex ($)" in e.columns:
        charts.line(e, "Prod Date", "Total Opex ($)", color="LSE_NAME", title="Total Opex ($) by LSE_NAME")
