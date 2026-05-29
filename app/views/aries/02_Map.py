import streamlit as st
from lib import charts, aries as A, model

st.title("Aries · Map")

wh = model.get_well_headers()
if wh is None:
    st.warning("Upload a well-headers CSV/xlsx in the sidebar (with Surface/Bottom Hole WGS84 columns)."); st.stop()


def find(cols, *needles):
    for c in cols:
        cl = c.lower()
        if all(n in cl for n in needles):
            return c
    return None


slat = find(wh.columns, "surface", "lat") or find(wh.columns, "lat")
slon = find(wh.columns, "surface", "lon") or find(wh.columns, "lon")
blat = find(wh.columns, "bottom", "lat")
blon = find(wh.columns, "bottom", "lon")
if not slat or not slon:
    st.error("Could not find latitude/longitude columns in the well headers."); st.stop()

df = wh.copy()

# Optional: size well heads by PV10 (AC_ONELINE) joined on API10
size_col = None
one = A.get_oneline(); prop = A.get_property()
api_wh = next((c for c in wh.columns if c.upper() in ("API10", "API12", "API14", "API")), None)
if one is not None and prop is not None and api_wh and "PV10 ($)" in one.columns and "API" in prop.columns:
    sel = st.session_state.get("aries_rsvcat_selection") or []
    pv = A.apply_rsvcat(one, sel).groupby("PROPNUM", as_index=False)["PV10 ($)"].sum()
    pv = pv.merge(prop[["PROPNUM", "API"]], on="PROPNUM", how="left")
    pv["__api10"] = model.normalize_api(pv["API"])
    df["__api10"] = model.normalize_api(df[api_wh])
    agg = pv.groupby("__api10", as_index=False)["PV10 ($)"].sum()
    df = df.merge(agg, on="__api10", how="left")
    if df["PV10 ($)"].notna().any():
        size_col = "PV10 ($)"

hover = next((c for c in ["Well Name", "Lease Name", "API14", "API10"] if c in df.columns), None)
st.caption("Horizontal/deviated wells are drawn surface→bottom-hole; vertical wells as a point. "
           "Marker size/color = PV10 when it can be matched by API.")
charts.well_map(df, slat, slon, blat, blon, hover=hover, size=size_col, title="Wells")
