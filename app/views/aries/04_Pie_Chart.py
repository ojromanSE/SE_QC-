import streamlit as st
from lib import charts, aries as A

st.title("Aries · Pie Chart — PV by LEASE_NAME")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
pv = charts.pv_select(e, "aries_pv_pie", default="PV20 ($)")
if pv is None or "LSE_NAME" not in e.columns:
    st.error("Need a PV column and LSE_NAME."); st.stop()
charts.pie(e, "LSE_NAME", pv, f"{pv} by LEASE_NAME")
