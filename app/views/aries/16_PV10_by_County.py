import streamlit as st
from lib import charts, aries as A

st.title("Aries · PV10 by County")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
if "County" in e.columns and "PV10 ($)" in e.columns:
    charts.treemap(e, ["County"], "PV10 ($)", "PV10 ($) by County")
    charts.show_table(e.groupby("County")["PV10 ($)"].sum().reset_index().sort_values("PV10 ($)", ascending=False),
                      money_cols=["PV10 ($)"])
else:
    st.error("Need County and PV10 ($).")
