"""Data Inspector — shows everything loaded and helps diagnose No-data issues."""
import streamlit as st
import pandas as pd
from lib import data_loader as dl

st.title("Data Inspector")
st.caption("Use this page to confirm your uploaded data matches what the report pages expect.")

store = dl.get_store()
if not store:
    st.warning("Nothing loaded yet. Use the sidebar uploaders.")
    st.stop()

st.subheader("Loaded tables")
summary = pd.DataFrame(
    [
        {"Table": k, "Rows": len(v), "Columns": len(v.columns)}
        for k, v in store.items()
        if not k.startswith("__") and hasattr(v, "columns")
    ]
).sort_values("Table")
st.dataframe(summary, hide_index=True, use_container_width=True)

aries = store.get("__aries__")
if aries:
    st.caption(f"Aries tables loaded (separate namespace): {len(aries)}")

EXPECTED = {
    "LseInfo": ["Lse_Id", "LSE_NAME", "RsvCat", "OPER", "County", "WrkInt", "RevInt"],
    "LseEco": [
        "Lse_Id", "EcoDate", "Net Oil (Bbl)", "Net Gas (Mcf)", "Net NGL (Bbl)",
        "Net Equivalent (Boe)", "Net Oil (Bbl/d)", "Net Gas (Mcf/d)", "Net NGL (Bbl/d)",
        "Net Equivalent (Boe/d)", "Gross Oil (Bbl/d)", "Gross Gas (Mcf/d)",
        "Gross NGL (Bbl/d)", "Gross Equivalent (Boe/d)",
        "Net Oil Revenue ($)", "Net Gas Revenue ($)", "Net NGL Revenue ($)",
        "Total Revenue ($)", "Total Opex ($)", "Total Sev Tax ($)",
        "Total Ad Val Tax ($)", "Total Investment ($)", "BFIT CF ($)",
        "PV8 ($)", "PV9 ($)", "PV10 ($)", "PV12 ($)", "PV15 ($)",
        "Opex ($/Boe)", "NGL Yield (Bbl/MMcf)", "Shrinkage",
        "Sev. Tax/Boe", "Ad Val Tax/Boe",
        "Sev. Tax $/Bbl", "Sev Tax $/Mcf", "Sev. Tax NGL $/Bbl",
        "Realized Oil Price ($/Bbl)", "Realized Gas Price ($/Mcf)",
        "F&D ($/Boe)", "Opex % of Revenue", "Net Capex ($)",
    ],
    "MonInfo": [
        "Lse_Id", "Prod Date",
        "Historical Oil Gross from Product (Bbl/d)",
        "Historical Gas Gross from Product (Mscf/d)",
        "Historical NGL Gross from Product (Bbl/d)",
        "Historical Equivalent Gross from Product (Boe/d)",
        "Net Historical Oil (Bbl/d)", "Net Historical Gas Sold (Mcf/d)",
        "Net Historical NGL (Bbl/d)", "Net Historical Equivalent (Boe/d)",
    ],
}

st.subheader("Column coverage vs report expectations")
for tname, expected in EXPECTED.items():
    df = store.get(tname)
    with st.expander(f"`{tname}` — {'loaded' if df is not None else 'NOT LOADED'}", expanded=(df is None)):
        if df is None:
            st.error(f"Table `{tname}` is not loaded. Upload PHDWin in the sidebar.")
            continue
        present = [c for c in expected if c in df.columns]
        missing = [c for c in expected if c not in df.columns]
        c1, c2 = st.columns(2)
        c1.metric("Expected columns present", f"{len(present)}/{len(expected)}")
        c2.metric("Total columns in table", len(df.columns))
        if missing:
            st.markdown("**Missing expected columns** (charts using these will say 'No data'):")
            st.code("\n".join(missing), language="text")
        st.markdown("**All columns in this table:**")
        st.code("\n".join(map(str, df.columns)), language="text")
        st.markdown("**First 5 rows:**")
        st.dataframe(df.head(), use_container_width=True)

st.subheader("Browse any loaded table")
choice = st.selectbox("Pick a table", sorted([k for k in store if not k.startswith("__")]))
if choice:
    df = store[choice]
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
    st.dataframe(df.head(500), use_container_width=True)
