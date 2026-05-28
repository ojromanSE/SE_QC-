import streamlit as st
from lib import charts, aries as A

st.title("Aries · Yield / Shrink Box Plot")
st.caption("AC_ONELINE is per-lease (no monthly date), so distributions are grouped by Reserve Category.")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
if "NGL Yield (Bbl/MMcf)" in e.columns:
    charts.box_by_group(e, "RsvCat", "NGL Yield (Bbl/MMcf)", sample="LSE_NAME", title="NGL Yield by RsvCat")
if "Shrinkage" in e.columns:
    charts.box_by_group(e, "RsvCat", "Shrinkage", sample="LSE_NAME", title="Shrinkage by RsvCat")
