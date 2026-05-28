import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Opex ($/Boe) vs Time")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
val = "Opex ($/Boe)"
if val not in e.columns:
    st.error(f"Need column `{val}`."); st.stop()

c1, c2 = st.columns([2, 1])
with c1:
    charts.box_by_group(e, "Year", val, sample="LSE_NAME", title="Opex ($/Boe) — Box plot by Year")
    yr = e.groupby("Year", dropna=False)[val].mean().reset_index().rename(columns={val: "Avg Opex ($/Boe)"})
    charts.show_table(yr)
with c2:
    charts.histogram(e, val, title="Opex ($/Boe) distribution")
