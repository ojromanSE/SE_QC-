import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Economics LOS Tie Out")

los = model.get_los_long()
eco = model.get_lse_eco()
if los is None:
    st.warning("Upload the LOS tie-out workbook (PowerBI_Long sheet)."); st.stop()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

mapping = [
    ("Total Operating Expense" if "Total Operating Expense" in los["Line Item"].unique() else "Operating Expense",
     "Total Opex ($)", "Opex — Reported vs Calculated"),
    ("Total Revenue", "Total Revenue ($)", "Revenue — Reported vs Calculated"),
]
for item, calc, title in mapping:
    if item in los["Line Item"].unique() and calc in e.columns:
        charts.los_tie_out_bars(los, item, e, "Prod Date", calc, title=title)
    else:
        st.info(f"Skipped {title} (missing `{item}` or `{calc}`).")

st.subheader("Differentials (Reported vs As-Of-Date Diff)")
st.caption("If your data store includes an `Asofdat` table with DiffValue / NGL Diff columns, add it via the PHDWin loader and update this page.")
