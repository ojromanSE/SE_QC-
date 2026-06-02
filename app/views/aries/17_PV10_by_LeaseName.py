import streamlit as st
from lib import charts, aries as A

st.title("Aries · PV by LEASE_NAME")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
pv = charts.pv_select(e, "aries_pv_lease")
if "LSE_NAME" in e.columns and pv:
    charts.treemap(e, ["LSE_NAME"], pv, f"{pv} by LEASE_NAME")
    charts.show_table(e.groupby("LSE_NAME")[pv].sum().reset_index().sort_values(pv, ascending=False),
                      money_cols=[pv])
else:
    st.error("Need LSE_NAME and a PV column.")
