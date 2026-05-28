import streamlit as st
from lib import charts, aries as A

st.title("Aries · PV10 by Operator")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
if "OPER" in e.columns and "PV10 ($)" in e.columns:
    charts.treemap(e, ["OPER"], "PV10 ($)", "PV10 ($) by Operator")
    charts.show_table(e.groupby("OPER")["PV10 ($)"].sum().reset_index().sort_values("PV10 ($)", ascending=False),
                      money_cols=["PV10 ($)"])
else:
    st.error("Need OPER and PV10 ($).")
