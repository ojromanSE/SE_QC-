import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Taxes Box Plot")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

for col, label in [("Sev. Tax/Boe", "Sev. Tax/Boe by Year"),
                   ("Ad Val Tax/Boe", "Ad Val Tax/Boe by Year")]:
    if col in e.columns:
        charts.box_by_group(e, "Year", col, sample="LSE_NAME", title=label)
