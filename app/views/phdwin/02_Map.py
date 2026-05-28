import streamlit as st
from lib import charts, model
from lib.filters import apply_rsvcat

st.title("Map")

wh = model.get_well_headers()
eco = model.get_lse_eco()
info = model.get_lse_info()
if wh is None:
    st.warning("Upload well headers CSV in the sidebar."); st.stop()

lat_cols = [c for c in wh.columns if "lat" in c.lower()]
lon_cols = [c for c in wh.columns if "lon" in c.lower()]
if not lat_cols or not lon_cols:
    st.error("Could not find latitude/longitude columns in well headers."); st.stop()

lat = st.selectbox("Latitude column", lat_cols, index=0)
lon = st.selectbox("Longitude column", lon_cols, index=0)

size_col = None
joined = wh.copy()
if eco is not None and info is not None:
    api_candidates = [c for c in wh.columns if c.upper() in ("API10", "API12", "API14", "API")]
    info_api = [c for c in info.columns if c.upper().startswith("API")]
    if api_candidates and info_api and "Lse_Id" in info.columns and "Lse_Id" in eco.columns:
        sel = st.session_state.get("rsvcat_selection") or []
        e_sum = apply_rsvcat(eco, sel)
        for pv in ("PV9 ($)", "PV10 ($)"):
            if pv in e_sum.columns:
                agg = e_sum.groupby("Lse_Id", as_index=False)[pv].sum().merge(
                    info[["Lse_Id", info_api[0]]], on="Lse_Id", how="left")
                agg[info_api[0]] = agg[info_api[0]].astype(str)
                joined[api_candidates[0]] = joined[api_candidates[0]].astype(str)
                joined = joined.merge(agg[[info_api[0], pv]],
                                       left_on=api_candidates[0], right_on=info_api[0], how="left")
                size_col = pv
                break

hover = next((c for c in ["Well Name", "Lease Name", "API14", "API10"] if c in joined.columns), None)
charts.well_map(joined, lat, lon, size=size_col, hover=hover, title="Wells (size = PV9/PV10)")
