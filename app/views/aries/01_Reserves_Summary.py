import streamlit as st
from lib import charts, aries as A

st.title("Aries · Reserves Summary")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)

vol = [c for c in ["Net Res Oil (Bbl)", "Net Res Gas (Mcf)", "Net Res NGL (Mcf)"] if c in e.columns]
if vol:
    t = e.groupby("RsvCat", dropna=False)[vol].sum().reset_index()
    charts.show_table(t, int_cols=vol)

pv = [c for c in ["BFIT CF ($)", "PV10 ($)", "PV15 ($)", "PV20 ($)", "PV25 ($)", "PV28 ($)"] if c in e.columns]
if pv:
    charts.show_table(e.groupby("RsvCat", dropna=False)[pv].sum().reset_index(), money_cols=pv)

c1, c2 = st.columns(2); c3, c4 = st.columns(2)
with c1: charts.pie(e, "RsvCat", "PV15 ($)", "PV15 ($) by RsvCat")
with c2: charts.pie(e, "RsvCat", "Net Res Oil (Bbl)", "Net Res Oil by RsvCat")
with c3: charts.pie(e, "RsvCat", "Net Res Gas (Mcf)", "Net Res Gas by RsvCat")
with c4: charts.pie(e, "RsvCat", "Net Res NGL (Mcf)", "Net Res NGL by RsvCat")
