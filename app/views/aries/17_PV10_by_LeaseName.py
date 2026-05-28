import streamlit as st
from lib import charts, aries as A

st.title("Aries · PV10 by LEASE_NAME")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
if "LSE_NAME" in e.columns and "PV10 ($)" in e.columns:
    charts.treemap(e, ["LSE_NAME"], "PV10 ($)", "PV10 ($) by LEASE_NAME")
    charts.show_table(e.groupby("LSE_NAME")["PV10 ($)"].sum().reset_index().sort_values("PV10 ($)", ascending=False),
                      money_cols=["PV10 ($)"])
else:
    st.error("Need LSE_NAME and PV10 ($).")
