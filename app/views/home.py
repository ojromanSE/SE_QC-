import streamlit as st

st.title("PHDWin / Aries QC")
st.write(
    "Streamlit replica of the SE QC PowerBI reports. Upload your database "
    "(PHDWin or Aries) in the sidebar, then use the grouped pages on the left."
)

store = st.session_state.get("store", {})
aries = store.get("__aries__") or {}
c = st.columns(3)
c[0].metric("PHDWin ready", "Yes" if ("LseEco" in store and "LseInfo" in store) else "No")
c[1].metric("Aries ready", "Yes" if ("AC_ONELINE" in aries and "AC_MONTHLY" in aries) else "No")
c[2].metric("Tables loaded", len([k for k in store if not k.startswith("__")]) + len(aries))

st.subheader("Quick start")
st.markdown(
    "- **PHDWin:** upload the `.accdb`/`.mdb` (zip it if the upload fails with a network error), "
    "or a pre-exported `.xlsx`. Tables: `LseInfo`, `LseEco`, `MonInfo`.\n"
    "- **Aries:** upload the `.mdb`/`.accdb` (or zip). Tables: `AC_PROPERTY`, `AC_ONELINE`, "
    "`AC_MONTHLY`, `AC_PRODUCT`.\n"
    "- **Well headers / LOS tie-out:** optional CSV / xlsx uploads used by the Map and LOS pages.\n"
    "- Both reports derive their PowerBI calculated columns automatically on upload."
)
