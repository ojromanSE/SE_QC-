import streamlit as st
from lib import charts, aries as A

st.title("Aries · Pie Chart — PV20 by LEASE_NAME")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
val = "PV20 ($)" if "PV20 ($)" in e.columns else ("PV10 ($)" if "PV10 ($)" in e.columns else None)
if val is None or "LSE_NAME" not in e.columns:
    st.error("Need a PV column and LSE_NAME."); st.stop()
charts.pie(e, "LSE_NAME", val, f"{val} by LEASE_NAME")
