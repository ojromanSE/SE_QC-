import streamlit as st
import pandas as pd
from lib import data_loader as dl

st.title("Aries QC")

store = dl.get_store()
aries = store.get("__aries__")
if aries is None:
    st.info(
        "Upload an Aries `.mdb` in the sidebar. Once you share a QC chart spec for Aries "
        "(table names, fields, desired visuals), this page will be wired up to match."
    )
    st.stop()

st.success(f"Aries tables loaded: {len(aries)}")
table = st.selectbox("Browse table", sorted(aries.keys()))
df: pd.DataFrame = aries[table]
st.caption(f"{len(df):,} rows × {len(df.columns)} cols")
st.dataframe(df.head(500), use_container_width=True)

st.subheader("Common Aries QC tables")
st.markdown(
    "- `AC_PROPERTY` — property header  \n"
    "- `AC_ECONOMIC` — economics input  \n"
    "- `AC_ONELINE` — oneline output  \n"
    "- `AC_PRODUCT` — production records  \n"
    "- `AC_DAILY` — daily forecast output"
)
st.caption(
    "Share which Aries fields you want QC'd (e.g. PV10, Net Reserves, F&D) and the visual style, "
    "and these will be implemented to match your existing PowerBI flow."
)
