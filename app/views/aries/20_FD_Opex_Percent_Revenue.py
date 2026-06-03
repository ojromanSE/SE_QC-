import streamlit as st
from lib import charts, aries as A

st.title("Aries · F&D, Opex % of Revenue")
st.caption(
    "F&D = total Net Capex ÷ total Net Equivalent (Boe) per Reserve Category.  "
    "Opex % of Revenue = volume-weighted Σ Total Opex ($) ÷ Σ Total Revenue ($) per month."
)
one = A.get_oneline(); mon = A.get_monthly()
sel = st.session_state.get("aries_rsvcat_selection") or []
if one is None and mon is None:
    st.warning("Upload an Aries database."); st.stop()

if one is not None:
    o = A.apply_rsvcat(one, sel)
    # F&D summary as a bar by Reserve Category (Σ Net Capex / Σ Net Equivalent Boe)
    if {"RsvCat", "Net Capex ($)", "Net Equivalent (Boe)"}.issubset(o.columns):
        import pandas as pd
        g = (o.groupby("RsvCat", dropna=False)[["Net Capex ($)", "Net Equivalent (Boe)"]]
               .sum().reset_index())
        g["F&D ($/BOE)"] = g["Net Capex ($)"] / g["Net Equivalent (Boe)"].replace(0, pd.NA)
        charts.show_table(g[["RsvCat", "Net Capex ($)", "Net Equivalent (Boe)", "F&D ($/BOE)"]],
                          money_cols=["Net Capex ($)", "F&D ($/BOE)"], int_cols=["Net Equivalent (Boe)"],
                          caption="F&D by Reserve Category")

if mon is not None:
    m = A.apply_rsvcat(mon, sel)
    if {"Total Opex ($)", "Total Revenue ($)"}.issubset(m.columns):
        # Weighted ratio over time = Σ opex / Σ revenue; *100 to read as a percent.
        m2 = m.copy()
        m2["Opex (% num)"] = m2["Total Opex ($)"] * 100  # scale so the weighted line is a percent
        charts.weighted_line(m2, "Prod Date", "Opex (% num)", "Total Revenue ($)",
                             title="Opex % of Revenue")
