import streamlit as st
import pandas as pd
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("F&D, Opex % of Revenue")
st.caption(
    "F&D = total Net Capex ÷ total Net Equivalent (Boe) per Reserve Category.  "
    "Opex % of Revenue = volume-weighted Σ Total Opex ($) ÷ Σ Total Revenue ($) per month."
)

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

# F&D summary per Reserve Category
if {"RsvCat", "Net Capex ($)", "Net Equivalent (Boe)"}.issubset(e.columns):
    g = (e.groupby("RsvCat", dropna=False)[["Net Capex ($)", "Net Equivalent (Boe)"]]
           .sum().reset_index())
    g["F&D ($/Boe)"] = g["Net Capex ($)"] / g["Net Equivalent (Boe)"].replace(0, pd.NA)
    charts.show_table(g[["RsvCat", "Net Capex ($)", "Net Equivalent (Boe)", "F&D ($/Boe)"]],
                      money_cols=["Net Capex ($)", "F&D ($/Boe)"], int_cols=["Net Equivalent (Boe)"],
                      caption="F&D by Reserve Category")

# Opex % of Revenue over time (volume-weighted)
dcol = "Prod Date" if "Prod Date" in e.columns else "EcoDate"
if {"Total Opex ($)", "Total Revenue ($)"}.issubset(e.columns):
    e2 = e.copy()
    e2["Opex (% num)"] = e2["Total Opex ($)"] * 100
    charts.weighted_line(e2, dcol, "Opex (% num)", "Total Revenue ($)",
                         title="Opex % of Revenue")
