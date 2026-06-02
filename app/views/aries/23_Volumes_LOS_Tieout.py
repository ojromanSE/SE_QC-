import streamlit as st
from lib import charts, aries as A, model

st.title("Aries · Volumes LOS Tie Out")
los = model.get_los_long()
mon = A.get_monthly()
if los is None:
    st.warning("Upload the LOS tie-out workbook in the sidebar (LOS_Data or PowerBI_Long sheet)."); st.stop()
if mon is None:
    st.warning("`AC_MONTHLY` is empty in this Aries export, so there's no calculated "
               "monthly stream to tie out against. Re-export after an Aries monthly run."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)

items = set(los["Line Item"].dropna().unique())
def pick(*cands):
    return next((c for c in cands if c in items), None)

mapping = [
    (pick("Oil Volume (BBLs)", "Oil Volume (MBBLs)"), "Gross Oil (Bbl)", "Oil — Reported vs Calculated"),
    (pick("Gas Volume (MCF)", "Gas Volume (MMCF)"), "Gross Gas (Mcf)", "Gas — Reported vs Calculated"),
    (pick("NGL Volume (BBLs)", "NGL Volume (MBBLs)"), "Gross NGL (Bbl)", "NGL — Reported vs Calculated"),
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
