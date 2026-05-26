import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Yield vs. Shrink")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

x = "Shrinkage"
y = next((c for c in ["NGL Yield1 (Bbl/MMcf)", "NGL Yield (Bbl/MMcf)"] if c in e.columns), None)
if x not in e.columns or y is None:
    st.error("Need Shrinkage and NGL Yield columns."); st.stop()
g = e.groupby("LSE_NAME", as_index=False).agg({x: "mean", y: "mean"})
charts.scatter(g, x, y, color="LSE_NAME", hover="LSE_NAME", title=f"{y} vs {x} (by LEASE_NAME)")
