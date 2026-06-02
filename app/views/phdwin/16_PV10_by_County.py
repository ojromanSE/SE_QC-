import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("PV by County")
eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
pv = charts.pv_select(e, "phd_pv_county")
if "County" in e.columns and pv:
    charts.treemap(e, ["County"], pv, title=f"{pv} by County")
    t = e.groupby("County", dropna=False)[pv].sum().reset_index().sort_values(pv, ascending=False)
    charts.show_table(t, money_cols=[pv])
else:
    st.error("Need County and a PV column.")
