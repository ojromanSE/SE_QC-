import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Reserves Summary")

eco = model.get_lse_eco()
info = model.get_lse_info()
if eco is None or info is None:
    st.warning("Load PHDWin first (need LseInfo + LseEco)."); st.stop()

sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

vol_cols = ["RsvCat"] + [c for c in ["Net Oil (Bbl)", "Net Gas (Mcf)", "Net NGL (Bbl)"] if c in e.columns]
vol = e.groupby("RsvCat", dropna=False)[[c for c in vol_cols if c != "RsvCat"]].sum().reset_index()
charts.show_table(vol, int_cols=[c for c in vol.columns if c != "RsvCat"])

pv_cols = [c for c in ["PV8 ($)", "PV9 ($)", "PV10 ($)", "PV12 ($)", "PV15 ($)", "BFIT CF ($)"] if c in e.columns]
if pv_cols:
    pv = e.groupby("RsvCat", dropna=False)[pv_cols].sum().reset_index()
    charts.show_table(pv, money_cols=pv_cols)

c1, c2 = st.columns(2)
c3, c4 = st.columns(2)
with c1: charts.pie(e, "RsvCat", "PV10 ($)", title="PV10 ($) by RsvCat")
with c2: charts.pie(e, "RsvCat", "Net Oil (Bbl)", title="Net Oil by RsvCat")
with c3:
    if "Net Gas (Mcf/d)" in e.columns: charts.pie(e, "RsvCat", "Net Gas (Mcf/d)", "Net Gas (Mcf/d) by RsvCat")
    elif "Net Gas (Mcf)" in e.columns: charts.pie(e, "RsvCat", "Net Gas (Mcf)", "Net Gas (Mcf) by RsvCat")
with c4: charts.pie(e, "RsvCat", "Net NGL (Bbl)", title="Net NGL by RsvCat")
