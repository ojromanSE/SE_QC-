import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("PV by LEASE_NAME")
eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
pv = charts.pv_select(e, "phd_pv_lease")
if "LSE_NAME" in e.columns and pv:
    charts.treemap(e, ["LSE_NAME"], pv, title=f"{pv} by LEASE_NAME")
    t = e.groupby("LSE_NAME", dropna=False)[pv].sum().reset_index().sort_values(pv, ascending=False)
    charts.show_table(t, money_cols=[pv])
else:
    st.error("Need LSE_NAME and a PV column.")
