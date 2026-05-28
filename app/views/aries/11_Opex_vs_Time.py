import streamlit as st
from lib import charts, aries as A

st.title("Aries · Opex ($/Boe) vs Time")
mon = A.get_monthly(); one = A.get_oneline()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
c1, c2 = st.columns([2, 1])
with c1:
    if "Opex ($/Boe)" in e.columns and "Year" in e.columns:
        charts.box_by_group(e, "Year", "Opex ($/Boe)", sample="LSE_NAME", title="Opex ($/Boe) — box by Year")
        yr = e.groupby("Year")["Opex ($/Boe)"].mean().reset_index().rename(columns={"Opex ($/Boe)": "Avg Opex ($/Boe)"})
        charts.show_table(yr)
with c2:
    o = A.apply_rsvcat(one, sel) if one is not None else None
    if o is not None and "Opex ($/Boe)" in o.columns:
        charts.histogram(o, "Opex ($/Boe)", title="Opex ($/Boe) distribution (oneline)")
