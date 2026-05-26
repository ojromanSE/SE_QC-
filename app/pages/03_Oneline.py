import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Oneline")

eco = model.get_lse_eco()
info = model.get_lse_info()
if eco is None or info is None:
    st.warning("Load PHDWin first."); st.stop()

sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)

sum_cols = [c for c in [
    "Net Oil (Bbl)", "Net Gas (Mcf)", "Net NGL (Bbl)", "Net Equivalent (Boe)",
    "BFIT CF ($)", "Total Revenue ($)", "Total Opex ($)", "Total Sev Tax ($)",
    "Total Ad Val Tax ($)", "Total Investment ($)", "PV9 ($)", "PV10 ($)",
] if c in e.columns]
group_cols = [c for c in ["LSE_NAME", "RsvCat"] if c in e.columns]
if "WrkInt" in info.columns or "RevInt" in info.columns:
    int_cols = [c for c in ["WrkInt", "RevInt"] if c in info.columns]
    int_df = info.groupby("LSE_NAME", as_index=False)[int_cols].mean()
else:
    int_df = None

t = e.groupby(group_cols, dropna=False)[sum_cols].sum().reset_index() if sum_cols else e[group_cols].drop_duplicates()
if int_df is not None and "LSE_NAME" in t.columns:
    t = t.merge(int_df, on="LSE_NAME", how="left")

money = [c for c in sum_cols if "$" in c]
ints = [c for c in sum_cols if c not in money]
charts.show_table(t, money_cols=money, int_cols=ints, height=600)
