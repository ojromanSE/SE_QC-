import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Yield / Shrink Box Plot")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

y = next((c for c in ["NGL Yield (Bbl/MMcf)", "NGL Yield1 (Bbl/MMcf)"] if c in e.columns), None)
if y:
    charts.box_by_group(e, "Year", y, sample="LSE_NAME", title=f"{y} by Year")
if "Shrinkage" in e.columns:
    charts.box_by_group(e, "Year", "Shrinkage", sample="LSE_NAME", title="Shrinkage by Year")
