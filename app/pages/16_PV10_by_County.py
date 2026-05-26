import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("PV10 by County")
eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
if "County" in e.columns and "PV10 ($)" in e.columns:
    charts.treemap(e, ["County"], "PV10 ($)", title="PV10 ($) by County")
    t = e.groupby("County", dropna=False)["PV10 ($)"].sum().reset_index().sort_values("PV10 ($)", ascending=False)
    charts.show_table(t, money_cols=["PV10 ($)"])
else:
    st.error("Need County and PV10 ($) columns.")
