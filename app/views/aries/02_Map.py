import streamlit as st
from lib import charts, aries as A

st.title("Aries · Map")
one = A.get_oneline()
prop = A.get_property()
if one is None or prop is None:
    st.warning("Upload an Aries database (needs AC_PROPERTY + AC_ONELINE)."); st.stop()
sel = st.session_state.get("aries_rsvcat_selection") or []

pv = A.apply_rsvcat(one, sel).groupby("PROPNUM", as_index=False)["PV10 ($)"].sum() if "PV10 ($)" in one.columns else None
df = prop.copy()
if pv is not None:
    df = df.merge(pv, on="PROPNUM", how="left")
if "Latitude" not in df.columns or "Longitude" not in df.columns:
    st.error("AC_PROPERTY has no LATITUDE/LONGITUDE."); st.stop()
charts.well_map(df, "Latitude", "Longitude", size="PV10 ($)" if pv is not None else None,
                hover="LSE_NAME" if "LSE_NAME" in df.columns else None, title="Wells (size = PV10)")
