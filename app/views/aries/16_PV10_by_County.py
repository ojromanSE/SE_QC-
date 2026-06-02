import streamlit as st
from lib import charts, aries as A

st.title("Aries · PV by County")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
pv = charts.pv_select(e, "aries_pv_county")
if "County" in e.columns and pv:
    charts.treemap(e, ["County"], pv, f"{pv} by County")
    charts.show_table(e.groupby("County")[pv].sum().reset_index().sort_values(pv, ascending=False),
                      money_cols=[pv])
else:
    st.error("Need County and a PV column.")
