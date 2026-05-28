import streamlit as st
import pandas as pd
from lib import data_loader as dl

st.title("Aries · Table Browser")

store = dl.get_store()
aries = store.get("__aries__")
if not aries:
    st.info("Upload an Aries `.mdb`/`.accdb` (or zip) in the sidebar.")
    st.stop()

st.caption("Browse the raw + enriched Aries tables (after PowerBI calculated columns are applied).")
table = st.selectbox("Table", sorted(aries.keys()))
df: pd.DataFrame = aries[table]
st.caption(f"{len(df):,} rows × {len(df.columns)} cols")
st.dataframe(df.head(500), use_container_width=True)
