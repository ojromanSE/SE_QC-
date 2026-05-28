import streamlit as st
from lib import charts, model

st.title("ResCat & API Check")

info = model.get_lse_info()
if info is None:
    st.warning("Load PHDWin first."); st.stop()

c1, c2 = st.columns(2)
with c1:
    st.subheader("LSE_NAME → RsvCat")
    cols = [c for c in ["LSE_NAME", "RsvCat"] if c in info.columns]
    if len(cols) == 2:
        charts.show_table(info[cols].drop_duplicates().sort_values("LSE_NAME"), height=500)
with c2:
    st.subheader("LSE_NAME + API")
    api_cols = [c for c in info.columns if c.upper().startswith("API")]
    cols = [c for c in (["LSE_NAME"] + api_cols) if c in info.columns]
    if cols:
        charts.show_table(info[cols].drop_duplicates().sort_values("LSE_NAME"), height=500)
