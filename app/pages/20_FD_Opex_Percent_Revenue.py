import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("F&D, Opex % of Revenue")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

if "F&D ($/Boe)" in e.columns and "RsvCat" in e.columns:
    charts.box_by_group(e, "RsvCat", "F&D ($/Boe)", sample="LSE_NAME", title="F&D ($/Boe) by RsvCat")
if "Opex % of Revenue" in e.columns and "Year" in e.columns:
    charts.box_by_group(e, "Year", "Opex % of Revenue", sample="LSE_NAME", title="Opex % of Revenue by Year")
