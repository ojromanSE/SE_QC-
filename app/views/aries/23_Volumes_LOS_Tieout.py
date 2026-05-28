import streamlit as st
from lib import charts, aries as A, model

st.title("Aries · Volumes LOS Tie Out")
los = model.get_los_long()
mon = A.get_monthly()
if los is None:
    st.warning("Upload the LOS tie-out workbook (sidebar) with a PowerBI_Long sheet."); st.stop()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
vol = los[los["Category"] == "Volumes"] if "Category" in los.columns else los
items = set(vol["Line Item"].unique())
mapping = [
    ("Oil Volume (MBBLs)", "Gross Oil (Bbl)", "Oil — Reported vs Calculated"),
    ("Gas Volume (MMCF)", "Gross Gas (Mcf)", "Gas — Reported vs Calculated"),
    ("NGL Volume (MBBLs)", "Gross NGL (Bbl)", "NGL — Reported vs Calculated"),
    ("Total (MBoe)", "Gross Equivalent (Boe/d)", "Boe — Reported vs Calculated"),
]
for item, calc, title in mapping:
    if item in items and calc in e.columns:
        charts.los_tie_out_bars(vol, item, e, "Prod Date", calc, title=title)
    else:
        st.info(f"Skipped {title} (missing `{item}` or `{calc}`).")
