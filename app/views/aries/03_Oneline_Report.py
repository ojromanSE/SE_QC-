import streamlit as st
from lib import charts, aries as A

st.title("Aries · Oneline Report")
one = A.get_oneline()
if one is None:
    st.warning("Upload an Aries database (needs AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(one, sel)

group = [c for c in ["LSE_NAME", "OPER", "RsvCat", "API"] if c in e.columns]
sums = [c for c in ["Initial Approx WI", "Initial Approx NRI", "Net Res Oil (Bbl)", "Net Res Gas (Mcf)",
                    "Net Res NGL (Mcf)", "Net Equivalent (Boe)", "Net Total Revenue ($)",
                    "Net Operating Expense ($)", "Net Capex ($)", "BFIT CF ($)", "PV10 ($)", "PV15 ($)"]
        if c in e.columns]
t = e.groupby(group, dropna=False)[sums].sum().reset_index() if sums else e[group].drop_duplicates()
money = [c for c in sums if "$" in c]
ints = [c for c in sums if c not in money and "Approx" not in c]
charts.show_table(t, money_cols=money, int_cols=ints, height=600)
