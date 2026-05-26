import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Pie Chart — PV10 by LEASE_NAME")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
if "PV10 ($)" not in e.columns or "LSE_NAME" not in e.columns:
    st.error("Need PV10 ($) and LSE_NAME columns."); st.stop()
charts.pie(e, "LSE_NAME", "PV10 ($)", title="PV10 ($) by LEASE_NAME")
