import streamlit as st
import plotly.express as px
from lib import aries as A, charts

st.title("Aries · Well Count")
mon = A.monthly_guard(st)
sel = st.session_state.get("aries_rsvcat_selection") or []
e = A.apply_rsvcat(mon, sel)
if "PROPNUM" not in e.columns or "Prod Date" not in e.columns:
    st.error("Need PROPNUM + Prod Date."); st.stop()
e = charts.filter_dates(e, "Prod Date")
g = e.dropna(subset=["PROPNUM", "Prod Date"]).groupby("Prod Date")["PROPNUM"].nunique().reset_index(name="Well Count")
fig = px.line(g, x="Prod Date", y="Well Count", title="Forecasted Well Count vs Prod Date")
fig.update_yaxes(type=charts.yaxis_type())
st.plotly_chart(fig, use_container_width=True)
