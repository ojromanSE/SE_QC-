"""Streamlit entry point for the PHDWin / Aries QC tool.

Replicates the 24-page PowerBI report `QC_Tool_PHDWin_v01.pbix` and adds
Aries database hooks.
"""
from __future__ import annotations
import streamlit as st

from lib import data_loader as dl
from lib.filters import rsvcat_filter

st.set_page_config(
    page_title="PHDWin / Aries QC",
    page_icon="OK",
    layout="wide",
)

PAGES = [
    ("00_Home", "Home"),
    ("01_Reserves_Summary", "Reserves Summary"),
    ("02_Map", "Map"),
    ("03_Oneline", "Oneline"),
    ("04_Pie_Chart", "Pie Chart"),
    ("05_Gross_Production", "Gross Production"),
    ("06_Net_Production", "Net Production"),
    ("07_Well_Count", "Well Count"),
    ("08_Net_Revenue", "Net Revenue"),
    ("09_Cash_Flow", "Cash Flow"),
    ("10_Net_CF_by_Case", "Net Cash Flow by Case"),
    ("11_Opex_vs_Time", "Opex ($/Boe) vs Time"),
    ("12_Yield_vs_Shrink_Plot", "Yield vs. Shrink Plot"),
    ("13_Yield_Shrink_Box", "Yield / Shrink Box Plot"),
    ("14_Taxes_Box", "Taxes Box Plot"),
    ("15_PV10_by_Operator", "PV10 by Operator"),
    ("16_PV10_by_County", "PV10 by County"),
    ("17_PV10_by_LeaseName", "PV10 by LEASE_NAME"),
    ("18_Reserves_Opex_Capex_Check", "Reserves, Opex, Capex Check"),
    ("19_ResCat_API_Check", "ResCat & API Check"),
    ("20_FD_Opex_Percent_Revenue", "F&D, Opex % of Revenue"),
    ("21_Sev_Tax_by_Phase", "Sev Tax by Phase"),
    ("22_Realized_Prices", "Realized Prices"),
    ("23_Volumes_LOS_Tieout", "Volumes LOS Tie Out"),
    ("24_Economics_LOS_Tieout", "Economics LOS Tie Out"),
    ("25_Aries_QC", "Aries QC (stub)"),
]


def sidebar_uploads():
    st.sidebar.header("Data")
    store = dl.get_store()

    with st.sidebar.expander("PHDWin database", expanded=True):
        st.caption("Upload a PHDWin .mdb (Linux: handled via mdbtools) or a pre-exported xlsx.")
        f = st.file_uploader("PHDWin .mdb / .xlsx", type=["mdb", "xlsx"], key="phd_upload")
        if f is not None:
            try:
                if f.name.lower().endswith(".mdb"):
                    tabs = dl.load_phdwin_mdb(f.getvalue(), f.name)
                else:
                    tabs = dl.load_phdwin_xlsx(f.getvalue())
                for k, v in tabs.items():
                    store[k] = v
                st.success(f"Loaded {len(tabs)} tables: {', '.join(list(tabs)[:6])}{'...' if len(tabs)>6 else ''}")
            except Exception as e:
                st.error(f"PHDWin load failed: {e}")

    with st.sidebar.expander("Aries database", expanded=False):
        st.caption("Upload an Aries .mdb. Aries pages are stubbed pending chart spec.")
        fa = st.file_uploader("Aries .mdb", type=["mdb"], key="aries_upload")
        if fa is not None:
            try:
                tabs = dl.load_phdwin_mdb(fa.getvalue(), fa.name)
                store["__aries__"] = tabs
                st.success(f"Aries tables loaded: {len(tabs)}")
            except Exception as e:
                st.error(f"Aries load failed: {e}")

    with st.sidebar.expander("Well headers (CSV)", expanded=False):
        fw = st.file_uploader("Well headers", type=["csv", "xlsx"], key="wh_upload")
        if fw is not None:
            try:
                store["well_headers"] = dl.load_well_headers(fw.getvalue(), fw.name)
                st.success(f"Well headers: {len(store['well_headers']):,} rows")
            except Exception as e:
                st.error(f"Well headers load failed: {e}")

    with st.sidebar.expander("LOS tie-out (xlsx)", expanded=False):
        st.caption("Workbook with a `PowerBI_Long` sheet: Date, Category, Line Item, Value.")
        fl = st.file_uploader("LOS xlsx", type=["xlsx"], key="los_upload")
        if fl is not None:
            try:
                tabs = dl.load_los_workbook(fl.getvalue())
                for k, v in tabs.items(): store[k] = v
                st.success(f"LOS sheets: {', '.join(tabs)}")
            except Exception as e:
                st.error(f"LOS load failed: {e}")

    st.sidebar.divider()
    st.sidebar.header("Loaded tables")
    if not store:
        st.sidebar.caption("Nothing loaded yet.")
    for k in sorted(store):
        if k.startswith("__"): continue
        v = store[k]
        try:
            st.sidebar.caption(f"`{k}` — {len(v):,} rows × {len(v.columns)} cols")
        except Exception:
            pass

    st.sidebar.divider()
    st.sidebar.header("Filters")
    rsvcat_filter()


def main():
    sidebar_uploads()
    st.title("PHDWin / Aries QC")
    st.write(
        "Streamlit replica of `QC_Tool_PHDWin_v01.pbix`. Upload your PHDWin database "
        "(or a pre-exported xlsx), well-headers CSV, and LOS tie-out workbook in the "
        "sidebar, then use the pages on the left to inspect each section."
    )
    cols = st.columns(3)
    cols[0].metric("PowerBI sections replicated", "24")
    store = st.session_state.get("store", {})
    cols[1].metric("Tables loaded", len([k for k in store if not k.startswith("__")]))
    has = "Yes" if "LseEco" in store and "LseInfo" in store else "No"
    cols[2].metric("PHDWin ready", has)

    st.subheader("Quick start")
    st.markdown(
        "- **PHDWin tables expected:** `LseInfo`, `LseEco`, `MonInfo`\n"
        "- **Well headers:** any CSV with surface lat/lon columns\n"
        "- **LOS tie-out:** xlsx with a `PowerBI_Long` sheet (Date, Category, Line Item, Value)\n"
        "- **Aries:** upload the .mdb; the dedicated Aries QC page is stubbed until you share a chart spec."
    )

    st.subheader("Sections")
    page_list = [name for _, name in PAGES if not name.startswith("Home")]
    grid = st.columns(3)
    for i, name in enumerate(page_list):
        grid[i % 3].markdown(f"- {name}")


if __name__ == "__main__":
    main()
