import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Economics LOS Tie Out")

los = model.get_los_long()
eco = model.get_lse_eco()
if los is None:
    st.warning("Upload the LOS tie-out workbook in the sidebar (LOS_Data or PowerBI_Long sheet)."); st.stop()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

items = set(los["Line Item"].dropna().unique())
def pick(*cands):
    return next((c for c in cands if c in items), None)

mapping = [
    (pick("Total OpEx", "Total Operating Expense", "Operating Expense"), "Total Opex ($)", "Opex — Reported vs Calculated"),
    (pick("Total Revenue"), "Total Revenue ($)", "Total Revenue — Reported vs Calculated"),
    (pick("Oil Revenue ($)", "Oil Revenue"), "Net Oil Revenue ($)", "Oil Revenue — Reported vs Calculated"),
    (pick("Gas Revenue ($)", "Gas Revenue"), "Net Gas Revenue ($)", "Gas Revenue — Reported vs Calculated"),
    (pick("NGL Revenue ($)", "NGL Revenue"), "Net NGL Revenue ($)", "NGL Revenue — Reported vs Calculated"),
]
any_shown = False
for item, calc, title in mapping:
    if item and calc in e.columns:
        charts.los_tie_out_bars(los, item, e, "Prod Date", calc, title=title)
        any_shown = True
    else:
        st.info(f"Skipped {title} (no matching LOS line item or `{calc}`).")
if not any_shown:
    st.caption("LOS line items found: " + ", ".join(sorted(items)))
