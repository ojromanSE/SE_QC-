import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Reserves, Opex, Capex Check")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

c1, c2, c3 = st.columns(3)
def by_lse(col, money=False):
    if "LSE_NAME" not in e.columns or col not in e.columns: return None
    t = e.groupby("LSE_NAME", dropna=False)[col].sum().reset_index().sort_values(col, ascending=False)
    return t

with c1:
    st.subheader("Net Equivalent (Boe)")
    t = by_lse("Net Equivalent (Boe)")
    if t is not None: charts.show_table(t, int_cols=["Net Equivalent (Boe)"])
with c2:
    st.subheader("Total Opex ($)")
    t = by_lse("Total Opex ($)")
    if t is not None: charts.show_table(t, money_cols=["Total Opex ($)"])
with c3:
    st.subheader("Net Capex ($)")
    t = by_lse("Net Capex ($)")
    if t is not None: charts.show_table(t, money_cols=["Net Capex ($)"])
