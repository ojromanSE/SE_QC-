import streamlit as st
from lib import charts, aries as A

st.title("Aries · ResCat & API Check")
prop = A.get_property()
if prop is None:
    st.warning("Upload an Aries database (needs AC_PROPERTY)."); st.stop()
c1, c2 = st.columns(2)
with c1:
    st.subheader("LEASE_NAME → RsvCat")
    cols = [c for c in ["LSE_NAME", "RsvCat"] if c in prop.columns]
    if len(cols) == 2:
        charts.show_table(prop[cols].drop_duplicates().sort_values("LSE_NAME"), height=500)
with c2:
    st.subheader("LEASE_NAME + API")
    cols = [c for c in ["LSE_NAME", "API"] if c in prop.columns]
    if cols:
        charts.show_table(prop[cols].drop_duplicates().sort_values("LSE_NAME"), height=500)
