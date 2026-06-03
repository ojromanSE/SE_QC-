import streamlit as st
from lib import charts, aries as A

st.title("Aries · Opex ($/Boe) vs Time")
st.caption("Volume-weighted Opex per BOE = Σ Total Opex ($) ÷ Σ Net Equivalent (Boe) per month.")
mon = A.get_monthly(); one = A.get_oneline()
if mon is None and one is None:
    st.warning("Upload an Aries database in the sidebar."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
c1, c2 = st.columns([2, 1])
with c1:
    if mon is not None:
        e = A.apply_rsvcat(mon, sel)
        if {"Total Opex ($)", "Net Equivalent (Boe)"}.issubset(e.columns):
            charts.weighted_line(e, "Prod Date", "Total Opex ($)", "Net Equivalent (Boe)",
                                 title="Opex ($/Boe) vs Time")
    else:
        st.info("`AC_MONTHLY` is empty — the monthly line needs a monthly Aries run. "
                "The oneline Opex distribution is shown at right.")
with c2:
    o = A.apply_rsvcat(one, sel) if one is not None else None
    if o is not None and "Opex ($/Boe)" in o.columns:
        charts.histogram(o, "Opex ($/Boe)", title="Opex ($/Boe) distribution (oneline)")
