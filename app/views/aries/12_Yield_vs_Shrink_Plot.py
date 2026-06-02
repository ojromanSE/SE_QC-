import streamlit as st
from lib import charts, aries as A

st.title("Aries · Yield vs. Shrink")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)
if "Shrinkage" not in e.columns or "NGL Yield (Bbl/MMcf)" not in e.columns:
    st.error("Need Shrinkage and NGL Yield (Bbl/MMcf)."); st.stop()
gb = ["LSE_NAME"] + (["SCENARIO"] if "SCENARIO" in e.columns else [])
g = e.groupby(gb, as_index=False).agg({"Shrinkage": "mean", "NGL Yield (Bbl/MMcf)": "mean"})
charts.scatter(g, "Shrinkage", "NGL Yield (Bbl/MMcf)", color="LSE_NAME", hover="LSE_NAME",
               title="NGL Yield vs Shrinkage (by LEASE_NAME)")
