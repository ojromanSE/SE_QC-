import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Net Revenue")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

c1, c2 = st.columns([2, 1])
phase_cols = [c for c in ["Net Oil Revenue ($)", "Net Gas Revenue ($)", "Net NGL Revenue ($)"] if c in e.columns]
with c1:
    if phase_cols and "Year" in e.columns:
        charts.grouped_column(e, "Year", phase_cols, title="Net Revenue by Phase by Year", barmode="stack")
with c2:
    if phase_cols:
        pivot = e[phase_cols].sum().reset_index()
        pivot.columns = ["Phase", "Value"]
        charts.pie(pivot, "Phase", "Value", title="Net Revenue by Phase")

c3, c4 = st.columns([2, 1])
with c3:
    if "Total Revenue ($)" in e.columns and "OPER" in e.columns and "Year" in e.columns:
        charts.stacked_column(e, "Year", "Total Revenue ($)", "OPER", title="Total Revenue by Operator by Year")
with c4:
    if "Total Revenue ($)" in e.columns and "OPER" in e.columns:
        charts.pie(e, "OPER", "Total Revenue ($)", title="Total Revenue by Operator")
