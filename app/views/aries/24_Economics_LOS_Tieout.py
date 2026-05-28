import streamlit as st
from lib import charts, aries as A, model

st.title("Aries · Economics LOS Tie Out")
los = model.get_los_long()
mon = A.get_monthly()
if los is None:
    st.warning("Upload the LOS tie-out workbook (sidebar) with a PowerBI_Long sheet."); st.stop()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
items = set(los["Line Item"].unique())
mapping = [
    ("Total Operating Expense" if "Total Operating Expense" in items else "Operating Expense",
     "Total Opex ($)", "Opex — Reported vs Calculated"),
    ("Total Revenue", "Total Revenue ($)", "Revenue — Reported vs Calculated"),
]
for item, calc, title in mapping:
    if item in items and calc in e.columns:
        charts.los_tie_out_bars(los, item, e, "Prod Date", calc, title=title)
    else:
        st.info(f"Skipped {title} (missing `{item}` or `{calc}`).")
