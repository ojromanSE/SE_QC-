import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Volumes LOS Tie Out")

los = model.get_los_long()
eco = model.get_lse_eco()
if los is None:
    st.warning("Upload the LOS tie-out workbook (PowerBI_Long sheet)."); st.stop()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

vol = los[los["Category"] == "Volumes"] if "Category" in los.columns else los
mapping = [
    ("Oil Volume (MBBLs)", "Gross Oil (BBl)", "Oil — Reported vs Calculated"),
    ("Gas Volume (MMCF)",  "Gross Gas (Mcf)", "Gas — Reported vs Calculated"),
    ("NGL Volume (MBBLs)", "Gross NGL (Bbl)", "NGL — Reported vs Calculated"),
    ("Total (MBoe)",        "Gross boe",       "Boe — Reported vs Calculated"),
]
for item, calc, title in mapping:
    if item in vol["Line Item"].unique() and calc in e.columns:
        charts.los_tie_out_bars(vol, item, e, "Prod Date", calc, title=title)
    else:
        st.info(f"Skipped {title} (missing `{item}` or `{calc}`).")
