import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Realized Prices")
st.caption("Volume-weighted realized price = Σ revenue ÷ Σ volume per period (not an average of per-lease prices).")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

dcol = "Prod Date" if "Prod Date" in e.columns else ("EcoDate" if "EcoDate" in e.columns else None)
if dcol is None:
    st.error("No date column on LseEco."); st.stop()

specs = [
    ("Net Oil Revenue ($)", "Net Oil (Bbl)", "Realized Oil Price ($/Bbl)"),
    ("Net Gas Revenue ($)", "Net Gas (Mcf)", "Realized Gas Price ($/Mcf)"),
    ("Net NGL Revenue ($)", "Net NGL (Bbl)", "Realized NGL Price ($/Bbl)"),
]
shown = False
for num, den, title in specs:
    if num in e.columns and den in e.columns:
        charts.weighted_line(e, dcol, num, den, title=title); shown = True
if not shown:
    if "Realized Oil Price ($/Bbl)" in e.columns:
        charts.line(e, dcol, "Realized Oil Price ($/Bbl)", title="Realized Oil Price ($/Bbl)")
    if "Realized Gas Price ($/Mcf)" in e.columns:
        charts.line(e, dcol, "Realized Gas Price ($/Mcf)", title="Realized Gas Price ($/Mcf)")
