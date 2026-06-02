"""Streamlit entry point for the PHDWin / Aries QC tool.

Replicates two SE QC PowerBI reports (PHDWin and Aries) as a grouped
multi-page Streamlit app. Sidebar uploads run on every page; navigation is
grouped into Overview / PHDWin QC / Aries QC via st.navigation.
"""
from __future__ import annotations
import streamlit as st

from lib import data_loader as dl
from lib import transform as tf
from lib import aries_transform as atf

st.set_page_config(page_title="PHDWin / Aries QC", layout="wide")


def _phd_uploader(store, expanded):
    with st.sidebar.expander("PHDWin database", expanded=expanded):
        st.caption("`.accdb`/`.mdb`, a **.zip** of it (if upload network-errors), or a pre-exported `.xlsx`.")
        f = st.file_uploader("PHDWin .accdb / .mdb / .zip / .xlsx",
                             type=["accdb", "mdb", "zip", "xlsx"], key="phd_upload")
        if f is not None:
            try:
                ext = f.name.lower().rsplit(".", 1)[-1]
                if ext in ("mdb", "accdb"):
                    tabs = dl.load_access_db(f.getvalue(), f.name, only_tables=dl.PHDWIN_NEEDED)
                elif ext == "zip":
                    tabs = dl.load_access_zip(f.getvalue(), f.name, only_tables=dl.PHDWIN_NEEDED)
                else:
                    tabs = dl.load_phdwin_xlsx(f.getvalue())
                for k, v in tabs.items():
                    store[k] = v
                st.success(f"Loaded {len(tabs)} tables: {', '.join(list(tabs)[:6])}")
            except Exception as e:
                st.error(f"PHDWin load failed: {e}")


def _aries_uploader(store, expanded):
    with st.sidebar.expander("Aries database", expanded=expanded):
        st.caption("`.mdb`/`.accdb` or a **.zip** of it. Reads AC_PROPERTY/ONELINE/MONTHLY/PRODUCT.")
        fa = st.file_uploader("Aries .mdb / .accdb / .zip / .xlsx", type=["mdb", "accdb", "zip", "xlsx"], key="aries_upload")
        if fa is not None:
            try:
                ext = fa.name.lower().rsplit(".", 1)[-1]
                if ext == "zip":
                    tabs = dl.load_access_zip(fa.getvalue(), fa.name, only_tables=dl.ARIES_NEEDED)
                elif ext == "xlsx":
                    tabs = dl.load_phdwin_xlsx(fa.getvalue())  # sheets named AC_PROPERTY/AC_ONELINE/...
                else:
                    tabs = dl.load_access_db(fa.getvalue(), fa.name, only_tables=dl.ARIES_NEEDED)
                # Copy out of the @st.cache_data result so enrichment / monthly-xls
                # appends don't mutate the cached object across reruns.
                store["__aries__"] = {k: v.copy() for k, v in tabs.items()}
                st.success(f"Aries tables loaded: {', '.join(sorted(tabs))}")
            except Exception as e:
                st.error(f"Aries load failed: {e}")
        st.caption("Add a monthly scenario from xls (a case not already in the .mdb):")
        fm = st.file_uploader("Monthly xls (AC_MONTHLY / Monthly Summary)", type=["xlsx"], key="aries_monthly_xls")
        scen_name = st.text_input("Scenario name for this monthly xls", value="", key="aries_monthly_scen")
        if fm is not None:
            try:
                n = dl.append_monthly_scenario(store, fm.getvalue(), scen_name or None)
                st.success(f"Appended {n:,} monthly rows as scenario `{scen_name or 'XLS'}`.")
            except Exception as e:
                st.error(f"Monthly xls load failed: {e}")


def _extras_uploader(store):
    with st.sidebar.expander("Well headers + LOS tie-out (optional)", expanded=False):
        fw = st.file_uploader("Well headers (CSV/xlsx)", type=["csv", "xlsx"], key="wh_upload")
        if fw is not None:
            try:
                store["well_headers"] = dl.load_well_headers(fw.getvalue(), fw.name)
                st.success(f"Well headers: {len(store['well_headers']):,} rows")
            except Exception as e:
                st.error(f"Well headers load failed: {e}")
        fl = st.file_uploader("LOS tie-out xlsx", type=["xlsx"], key="los_upload")
        if fl is not None:
            try:
                for k, v in dl.load_los_workbook(fl.getvalue()).items():
                    store[k] = v
                st.success("LOS workbook loaded.")
            except Exception as e:
                st.error(f"LOS load failed: {e}")


def _clear_data():
    """Reset the loaded data + uploader widgets so the user can switch source."""
    st.session_state["store"] = {}
    for k in ["phd_upload", "aries_upload", "aries_monthly_xls", "aries_monthly_scen",
              "wh_upload", "los_upload", "rsvcat_selection", "aries_scenarios",
              "aries_rsvcat_selection", "aries_scn_mode", "chart_date_range"]:
        st.session_state.pop(k, None)


def sidebar_uploads():
    store = dl.get_store()
    phd_loaded = ("LseEco" in store) or ("LseInfo" in store)
    ar = store.get("__aries__") or {}
    aries_loaded = bool(ar) and (("AC_ONELINE" in ar) or ("AC_MONTHLY" in ar))

    # --- Step 1: data ------------------------------------------------------
    st.sidebar.header("Step 1 · Data")
    if not (phd_loaded or aries_loaded):
        # Nothing loaded yet — offer both database uploaders.
        _phd_uploader(store, expanded=True)
        _aries_uploader(store, expanded=True)
    elif aries_loaded and not phd_loaded:
        st.sidebar.caption("Aries data loaded.")
        _aries_uploader(store, expanded=False)
        with st.sidebar.expander("Use PHDWin instead", expanded=False):
            st.caption("Loading PHDWin starts a separate workflow.")
            _phd_uploader(store, expanded=True)
    elif phd_loaded and not aries_loaded:
        st.sidebar.caption("PHDWin data loaded.")
        _phd_uploader(store, expanded=False)
        with st.sidebar.expander("Use Aries instead", expanded=False):
            st.caption("Loading Aries starts a separate workflow.")
            _aries_uploader(store, expanded=True)
    else:  # both loaded
        _phd_uploader(store, expanded=False)
        _aries_uploader(store, expanded=False)

    _extras_uploader(store)
    if phd_loaded or aries_loaded:
        st.sidebar.button("Clear data / switch source", on_click=_clear_data, use_container_width=True)

    # Derive PowerBI calculated columns for whichever sources are present.
    tf.enrich_store(store)
    atf.enrich_aries_store(store)


def _data_date_span(store: dict):
    """Min/max date across loaded time-series tables, for the date-range anchor."""
    import pandas as pd
    mins, maxs = [], []
    frames = [store.get("LseEco"), store.get("MonInfo"), store.get("los_long"), store.get("PowerBI_Long")]
    aries = store.get("__aries__") or {}
    frames += [aries.get("AC_MONTHLY"), aries.get("AC_PRODUCT")]
    for df in frames:
        if df is None:
            continue
        for col in ["Prod Date", "OUTDATE", "P_DATE", "EcoDate", "Date"]:
            if col in df.columns:
                s = pd.to_datetime(df[col], errors="coerce").dropna()
                if not s.empty:
                    mins.append(s.min()); maxs.append(s.max())
                break
    if mins and maxs:
        return min(mins).date(), max(maxs).date()
    return None


def render_top_filters(store: dict, phd_loaded: bool, aries_loaded: bool):
    """Render the global filters as a bar at the top of the main content area
    (above each page's title), instead of in the sidebar, so they stay handy
    while working through a page's visualizations."""
    if not (phd_loaded or aries_loaded):
        return
    from lib import aries as A

    with st.container(border=True):
        widgets = []  # (label-less) render callables, laid out in equal columns

        if aries_loaded:
            scen_opts = A.scenario_options()
            if scen_opts:
                default_scen = A.default_scenario()
                st.session_state.setdefault("aries_scenarios", [default_scen] if default_scen else scen_opts[:1])
                widgets.append(lambda c: c.multiselect(
                    "Scenario(s)", scen_opts, key="aries_scenarios",
                    help="Pick one case, or two+ to compare."))
            if len(st.session_state.get("aries_scenarios") or []) > 1:
                st.session_state.setdefault("aries_scn_mode", "Overlay")
                widgets.append(lambda c: c.radio(
                    "Multi-scenario view", ["Overlay", "Split"], horizontal=True, key="aries_scn_mode",
                    help="Overlay = scenarios as series on one chart. Split = a panel per scenario."))
            aopts = A.rsvcat_options()
            if aopts:
                st.session_state.setdefault("aries_rsvcat_selection", aopts)
                widgets.append(lambda c: c.multiselect("Reserve category", aopts, key="aries_rsvcat_selection"))

        if phd_loaded:
            lse = store.get("LseInfo")
            if lse is not None and "RsvCat" in lse.columns:
                opts = sorted(lse["RsvCat"].dropna().unique().tolist())
                st.session_state.setdefault("rsvcat_selection", opts)
                widgets.append(lambda c: c.multiselect("Reserve category", opts, key="rsvcat_selection"))

        # Y-axis scale always available
        widgets.append(_scale_widget)

        cols = st.columns(len(widgets))
        for render, col in zip(widgets, cols):
            render(col)

        _date_widget(store)


def _scale_widget(col):
    scale = col.radio("Y-axis scale", ["Linear", "Log"], horizontal=True, key="chart_yscale_label")
    st.session_state["chart_yscale"] = "log" if scale == "Log" else "linear"


def _date_widget(store: dict):
    span = _data_date_span(store)
    if not span:
        st.session_state["chart_date_range"] = None
        return
    anchor = st.checkbox("Anchor date range", value=False, key="chart_date_anchor")
    if anchor:
        dr = st.date_input("Date range", value=span, min_value=span[0], max_value=span[1], key="chart_date_input")
        st.session_state["chart_date_range"] = dr if isinstance(dr, (list, tuple)) and len(dr) == 2 else None
    else:
        st.session_state["chart_date_range"] = None


def _pg(path: str, title: str, icon: str = ""):
    # st.Page resolves the script path relative to the entrypoint (app.py), so
    # use a path relative to app/. Unique url_path per page because st.Page
    # derives the URL from the filename stem and ignores the folder, so the
    # same-named phdwin/ and aries/ files would otherwise collide.
    slug = path.replace("/", "_").replace(".py", "")
    return st.Page(f"views/{path}", title=title, icon=icon or None, url_path=slug)


def main():
    sidebar_uploads()

    phdwin = [
        _pg("phdwin/01_Reserves_Summary.py", "Reserves Summary"),
        _pg("phdwin/02_Map.py", "Map"),
        _pg("phdwin/03_Oneline.py", "Oneline"),
        _pg("phdwin/04_Pie_Chart.py", "Pie Chart"),
        _pg("phdwin/05_Gross_Production.py", "Gross Production"),
        _pg("phdwin/06_Net_Production.py", "Net Production"),
        _pg("phdwin/07_Well_Count.py", "Well Count"),
        _pg("phdwin/08_Net_Revenue.py", "Net Revenue"),
        _pg("phdwin/09_Cash_Flow.py", "Cash Flow"),
        _pg("phdwin/10_Net_CF_by_Case.py", "Net Cash Flow by Case"),
        _pg("phdwin/11_Opex_vs_Time.py", "Opex ($/Boe) vs Time"),
        _pg("phdwin/12_Yield_vs_Shrink_Plot.py", "Yield vs. Shrink Plot"),
        _pg("phdwin/13_Yield_Shrink_Box.py", "Yield / Shrink Box Plot"),
        _pg("phdwin/14_Taxes_Box.py", "Taxes Box Plot"),
        _pg("phdwin/15_PV10_by_Operator.py", "PV by Operator"),
        _pg("phdwin/16_PV10_by_County.py", "PV by County"),
        _pg("phdwin/17_PV10_by_LeaseName.py", "PV by LEASE_NAME"),
        _pg("phdwin/18_Reserves_Opex_Capex_Check.py", "Reserves, Opex, Capex Check"),
        _pg("phdwin/19_ResCat_API_Check.py", "ResCat & API Check"),
        _pg("phdwin/20_FD_Opex_Percent_Revenue.py", "F&D, Opex % of Revenue"),
        _pg("phdwin/21_Sev_Tax_by_Phase.py", "Sev Tax by Phase"),
        _pg("phdwin/22_Realized_Prices.py", "Realized Prices"),
        _pg("phdwin/23_Volumes_LOS_Tieout.py", "Volumes LOS Tie Out"),
        _pg("phdwin/24_Economics_LOS_Tieout.py", "Economics LOS Tie Out"),
    ]
    aries = [
        _pg("aries/01_Reserves_Summary.py", "Reserves Summary"),
        _pg("aries/02_Map.py", "Map"),
        _pg("aries/03_Oneline_Report.py", "Oneline Report"),
        _pg("aries/04_Pie_Chart.py", "Pie Chart"),
        _pg("aries/05_Gross_Production.py", "Gross Production"),
        _pg("aries/06_Net_Production.py", "Net Production"),
        _pg("aries/07_Well_Count.py", "Well Count"),
        _pg("aries/08_Net_Revenue.py", "Net Revenue"),
        _pg("aries/09_Cash_Flow.py", "Cash Flow"),
        _pg("aries/10_Net_CF_by_Case.py", "Net Cash Flow by Case"),
        _pg("aries/11_Opex_vs_Time.py", "Opex ($/Boe) vs Time"),
        _pg("aries/12_Yield_vs_Shrink_Plot.py", "Yield vs. Shrink Plot"),
        _pg("aries/13_Yield_Shrink_Box.py", "Yield / Shrink Box Plot"),
        _pg("aries/14_Taxes_Box.py", "Taxes Box Plot"),
        _pg("aries/15_PV10_by_Operator.py", "PV by Operator"),
        _pg("aries/16_PV10_by_County.py", "PV by County"),
        _pg("aries/17_PV10_by_LeaseName.py", "PV by LEASE_NAME"),
        _pg("aries/18_Reserves_Opex_Capex_Check.py", "Reserves, Opex, Capex Check"),
        _pg("aries/19_ResCat_API_Check.py", "ResCat & API Check"),
        _pg("aries/20_FD_Opex_Percent_Revenue.py", "F&D, Opex % of Revenue"),
        _pg("aries/21_Sev_Tax_by_Phase.py", "Sev Tax by Phase"),
        _pg("aries/22_Realized_Prices.py", "Realized Prices"),
        _pg("aries/23_Volumes_LOS_Tieout.py", "Volumes LOS Tie Out"),
        _pg("aries/24_Economics_LOS_Tieout.py", "Economics LOS Tie Out"),
        _pg("aries_browser.py", "Table Browser"),
    ]
    inspector = _pg("data_inspector.py", "Data Inspector")

    store = dl.get_store()
    phd_loaded = ("LseEco" in store) or ("LseInfo" in store)
    ar = store.get("__aries__") or {}
    aries_loaded = bool(ar) and (("AC_ONELINE" in ar) or ("AC_MONTHLY" in ar))

    # Order so the default landing page matches the loaded source.
    if aries_loaded and not phd_loaded:
        ordered = aries + phdwin + [inspector]
    else:
        ordered = phdwin + aries + [inspector]

    # Hide the built-in nav; we render our own links in the sidebar below the
    # data + filter steps so the order is data -> filters -> visualizations.
    nav = st.navigation(ordered, position="hidden")

    # --- Step 2: visualizations (source-aware page links) ------------------
    st.sidebar.divider()
    st.sidebar.header("Step 2 · Visualizations")
    if aries_loaded:
        if phd_loaded:
            st.sidebar.caption("**Aries QC**")
        for p in aries:
            st.sidebar.page_link(p)
    if phd_loaded:
        if aries_loaded:
            st.sidebar.caption("**PHDWin QC**")
        for p in phdwin:
            st.sidebar.page_link(p)
    if not (phd_loaded or aries_loaded):
        st.sidebar.caption("Upload data above to see the visualizations.")
    st.sidebar.divider()
    st.sidebar.page_link(inspector)

    # Filters render as a bar at the top of the main area, above the page title.
    render_top_filters(store, phd_loaded, aries_loaded)
    nav.run()


if __name__ == "__main__":
    main()
