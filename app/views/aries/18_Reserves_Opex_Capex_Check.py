import streamlit as st
from lib import charts, aries as A

st.title("Aries · Reserves, Opex, Capex Check")
one = A.get_oneline(); mon = A.get_monthly()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
o = A.apply_rsvcat(one, sel)
m = A.apply_rsvcat(mon, sel) if mon is not None else None

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Net Equivalent (Boe)")
    if "Net Equivalent (Boe)" in o.columns:
        charts.show_table(o.groupby("LSE_NAME")["Net Equivalent (Boe)"].sum().reset_index()
                          .sort_values("Net Equivalent (Boe)", ascending=False), int_cols=["Net Equivalent (Boe)"])
with c2:
    st.subheader("Total Opex ($)")
    if m is not None and "Total Opex ($)" in m.columns:
        charts.show_table(m.groupby("LSE_NAME")["Total Opex ($)"].sum().reset_index()
                          .sort_values("Total Opex ($)", ascending=False), money_cols=["Total Opex ($)"])
with c3:
    st.subheader("Net Capex ($)")
    if "Net Capex ($)" in o.columns:
        charts.show_table(o.groupby("LSE_NAME")["Net Capex ($)"].sum().reset_index()
                          .sort_values("Net Capex ($)", ascending=False), money_cols=["Net Capex ($)"])
