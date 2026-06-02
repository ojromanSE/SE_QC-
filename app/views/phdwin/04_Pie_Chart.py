import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Pie Chart — PV by LEASE_NAME")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
pv = charts.pv_select(e, "phd_pv_pie")
if pv is None or "LSE_NAME" not in e.columns:
    st.error("Need a PV column and LSE_NAME."); st.stop()
charts.pie(e, "LSE_NAME", pv, title=f"{pv} by LEASE_NAME")
