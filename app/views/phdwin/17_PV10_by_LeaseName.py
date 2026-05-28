import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("PV10 by LEASE_NAME")
eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
if "LSE_NAME" in e.columns and "PV10 ($)" in e.columns:
    charts.treemap(e, ["LSE_NAME"], "PV10 ($)", title="PV10 ($) by LEASE_NAME")
    t = e.groupby("LSE_NAME", dropna=False)["PV10 ($)"].sum().reset_index().sort_values("PV10 ($)", ascending=False)
    charts.show_table(t, money_cols=["PV10 ($)"])
else:
    st.error("Need LSE_NAME and PV10 ($) columns.")
