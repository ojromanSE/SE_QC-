import streamlit as st
from lib import charts, aries as A

st.title("Aries · Realized Prices")
st.caption("Volume-weighted realized price = Σ revenue ÷ Σ volume per month (not an average of per-well prices).")
mon = A.monthly_guard(st)
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)

specs = [
    ("Net Oil Revenue ($)", "Net Oil (Bbl)", "Realized Oil Price ($/Bbl)"),
    ("Net Gas Revenue ($)", "Net Gas (Mcf)", "Realized Gas Price ($/Mcf)"),
    ("Net NGL Revenue ($)", "Net NGL (Bbl)", "Realized NGL Price ($/Bbl)"),
]
shown = False
for num, den, title in specs:
    if num in e.columns and den in e.columns:
        charts.weighted_line(e, "Prod Date", num, den, title=title); shown = True
if not shown:
    # Fallback: if only the pre-computed price columns exist, show them directly.
    if "Oil Price ($/bbl)" in e.columns:
        charts.line(e, "Prod Date", "Oil Price ($/bbl)", title="Oil Price ($/bbl)")
    if "Gas Price ($/Mcf)" in e.columns:
        charts.line(e, "Prod Date", "Gas Price ($/Mcf)", title="Gas Price ($/Mcf)")
