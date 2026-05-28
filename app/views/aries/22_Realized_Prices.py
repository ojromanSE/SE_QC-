import streamlit as st
from lib import charts, aries as A

st.title("Aries · Realized Prices")
mon = A.get_monthly()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
if "Oil Price ($/bbl)" in e.columns:
    charts.line(e, "Prod Date", "Oil Price ($/bbl)", title="Oil Price ($/bbl)")
if "Gas Price ($/Mcf)" in e.columns:
    charts.line(e, "Prod Date", "Gas Price ($/Mcf)", title="Gas Price ($/Mcf)")
