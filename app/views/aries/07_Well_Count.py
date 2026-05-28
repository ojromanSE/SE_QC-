import streamlit as st
import plotly.express as px
from lib import aries as A

st.title("Aries · Well Count")
mon = A.get_monthly()
if mon is None:
    st.warning("Upload an Aries database (needs AC_MONTHLY)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
if "PROPNUM" not in e.columns or "Prod Date" not in e.columns:
    st.error("Need PROPNUM + Prod Date."); st.stop()
g = e.dropna(subset=["PROPNUM", "Prod Date"]).groupby("Prod Date")["PROPNUM"].nunique().reset_index(name="Well Count")
st.plotly_chart(px.line(g, x="Prod Date", y="Well Count", title="Forecasted Well Count vs Prod Date"),
                use_container_width=True)
