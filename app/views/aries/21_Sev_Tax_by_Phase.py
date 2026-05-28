import streamlit as st
from lib import charts, aries as A

st.title("Aries · Sev Tax by Phase")
mon = A.get_monthly()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
for col, label in [("Sev Tax/Bbl", "Sev Tax $/Bbl (Oil)"),
                   ("Sev Tax/Mcf", "Sev Tax $/Mcf (Gas)"),
                   ("Sev Tax/BNGL", "Sev Tax $/Bbl (NGL)")]:
    if col in e.columns and "Year" in e.columns:
        charts.box_by_group(e, "Year", col, sample="LSE_NAME", title=label)
