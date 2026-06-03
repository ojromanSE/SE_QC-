import streamlit as st
from lib import model, charts
from lib.filters import apply_rsvcat
import plotly.express as px

st.title("Well Count")

eco = model.get_lse_eco()
if eco is None:
    st.warning("Load PHDWin first."); st.stop()
sel = st.session_state.get("rsvcat_selection") or []
e = apply_rsvcat(eco, sel)
if "Lse_Id" not in e.columns or "Prod Date" not in e.columns:
    st.error("Need Lse_Id + Prod Date."); st.stop()

e = charts.filter_dates(e, "Prod Date")
g = e.dropna(subset=["Lse_Id", "Prod Date"]).groupby("Prod Date")["Lse_Id"].nunique().reset_index(name="Well Count")
fig = px.line(g, x="Prod Date", y="Well Count", title="Well Count vs Prod Date")
fig.update_yaxes(type=charts.yaxis_type())
charts._show(fig)
