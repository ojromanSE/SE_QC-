import streamlit as st
from lib import charts, aries as A

st.title("Aries · F&D, Opex % of Revenue")
one = A.get_oneline(); mon = A.get_monthly()
sel = st.session_state.get("aries_rsvcat_selection") or []
if one is not None:
    o = A.apply_rsvcat(one, sel)
    if "F&D ($/BOE)" in o.columns and "RsvCat" in o.columns:
        charts.box_by_group(o, "RsvCat", "F&D ($/BOE)", sample="LSE_NAME", title="F&D ($/BOE) by RsvCat")
if mon is not None:
    m = A.apply_rsvcat(mon, sel)
    if "Opex % of Revenue" in m.columns and "Year" in m.columns:
        charts.box_by_group(m, "Year", "Opex % of Revenue", sample="LSE_NAME", title="Opex % of Revenue by Year")
if one is None and mon is None:
    st.warning("Upload an Aries database.")
