import streamlit as st
from lib import charts, aries as A

st.title("Aries · Net Revenue")
mon = A.monthly_guard(st)
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
phase = [c for c in ["Net Oil Revenue ($)", "Net Gas Revenue ($)", "Net NGL Revenue ($)"] if c in e.columns]

c1, c2 = st.columns([2, 1])
with c1:
    if phase and "Year" in e.columns:
        charts.grouped_column(e, "Year", phase, title="Net Revenue by Phase by Year", barmode="stack")
with c2:
    if phase:
        p = e[phase].sum().reset_index(); p.columns = ["Phase", "Value"]
        charts.pie(p, "Phase", "Value", "Net Revenue by Phase")

c3, c4 = st.columns([2, 1])
with c3:
    if "Total Revenue ($)" in e.columns and "OPER" in e.columns and "Year" in e.columns:
        charts.stacked_column(e, "Year", "Total Revenue ($)", "OPER", "Total Revenue by Operator by Year")
with c4:
    if "Total Revenue ($)" in e.columns and "OPER" in e.columns:
        charts.pie(e, "OPER", "Total Revenue ($)", "Total Revenue by Operator")
