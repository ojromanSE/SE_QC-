"""Full-report export: run every visualization page headlessly with the
current filters and assemble one combined PDF.

The page scripts are normal Streamlit scripts. To collect their figures
without rendering to the live UI, we set `pdf_export.COLLECT_ONLY` (so the
chart helpers skip the Options popover / PV selectbox), monkeypatch the
Streamlit output + layout functions to no-ops for the duration, and exec each
page, catching `_CollectStop` (raised by our patched `st.stop`).
"""
from __future__ import annotations
import os
from typing import List, Tuple

from . import pdf_export

VIEWS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "views")

PHDWIN_SPECS = [
    ("phdwin/01_Reserves_Summary.py", "Reserves Summary"),
    ("phdwin/02_Map.py", "Map"),
    ("phdwin/03_Oneline.py", "Oneline"),
    ("phdwin/04_Pie_Chart.py", "Pie Chart"),
    ("phdwin/05_Gross_Production.py", "Gross Production"),
    ("phdwin/06_Net_Production.py", "Net Production"),
    ("phdwin/07_Well_Count.py", "Well Count"),
    ("phdwin/08_Net_Revenue.py", "Net Revenue"),
    ("phdwin/09_Cash_Flow.py", "Cash Flow"),
    ("phdwin/10_Net_CF_by_Case.py", "Net Cash Flow by Case"),
    ("phdwin/11_Opex_vs_Time.py", "Opex ($/Boe) vs Time"),
    ("phdwin/12_Yield_vs_Shrink_Plot.py", "Yield vs. Shrink Plot"),
    ("phdwin/13_Yield_Shrink_Box.py", "Yield / Shrink Box Plot"),
    ("phdwin/14_Taxes_Box.py", "Taxes Box Plot"),
    ("phdwin/15_PV10_by_Operator.py", "PV by Operator"),
    ("phdwin/16_PV10_by_County.py", "PV by County"),
    ("phdwin/17_PV10_by_LeaseName.py", "PV by LEASE_NAME"),
    ("phdwin/18_Reserves_Opex_Capex_Check.py", "Reserves, Opex, Capex Check"),
    ("phdwin/19_ResCat_API_Check.py", "ResCat & API Check"),
    ("phdwin/20_FD_Opex_Percent_Revenue.py", "F&D, Opex % of Revenue"),
    ("phdwin/21_Sev_Tax_by_Phase.py", "Sev Tax by Phase"),
    ("phdwin/22_Realized_Prices.py", "Realized Prices"),
    ("phdwin/23_Volumes_LOS_Tieout.py", "Volumes LOS Tie Out"),
    ("phdwin/24_Economics_LOS_Tieout.py", "Economics LOS Tie Out"),
]
ARIES_SPECS = [
    ("aries/01_Reserves_Summary.py", "Reserves Summary"),
    ("aries/02_Map.py", "Map"),
    ("aries/03_Oneline_Report.py", "Oneline Report"),
    ("aries/04_Pie_Chart.py", "Pie Chart"),
    ("aries/05_Gross_Production.py", "Gross Production"),
    ("aries/06_Net_Production.py", "Net Production"),
    ("aries/07_Well_Count.py", "Well Count"),
    ("aries/08_Net_Revenue.py", "Net Revenue"),
    ("aries/09_Cash_Flow.py", "Cash Flow"),
    ("aries/10_Net_CF_by_Case.py", "Net Cash Flow by Case"),
    ("aries/11_Opex_vs_Time.py", "Opex ($/Boe) vs Time"),
    ("aries/12_Yield_vs_Shrink_Plot.py", "Yield vs. Shrink Plot"),
    ("aries/13_Yield_Shrink_Box.py", "Yield / Shrink Box Plot"),
    ("aries/14_Taxes_Box.py", "Taxes Box Plot"),
    ("aries/15_PV10_by_Operator.py", "PV by Operator"),
    ("aries/16_PV10_by_County.py", "PV by County"),
    ("aries/17_PV10_by_LeaseName.py", "PV by LEASE_NAME"),
    ("aries/18_Reserves_Opex_Capex_Check.py", "Reserves, Opex, Capex Check"),
    ("aries/19_ResCat_API_Check.py", "ResCat & API Check"),
    ("aries/20_FD_Opex_Percent_Revenue.py", "F&D, Opex % of Revenue"),
    ("aries/21_Sev_Tax_by_Phase.py", "Sev Tax by Phase"),
    ("aries/22_Realized_Prices.py", "Realized Prices"),
    ("aries/23_Volumes_LOS_Tieout.py", "Volumes LOS Tie Out"),
    ("aries/24_Economics_LOS_Tieout.py", "Economics LOS Tie Out"),
]


class _Dummy:
    """Stand-in for Streamlit layout objects during headless export."""
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __call__(self, *a, **k): return self
    def __getattr__(self, n): return self
    def __iter__(self): return iter([])


class _CollectStop(Exception):
    pass


def _run_page_collect(relpath: str, title: str):
    pdf_export.reset(title)
    path = os.path.join(VIEWS_DIR, relpath)
    try:
        with open(path) as fh:
            code = compile(fh.read(), path, "exec")
        exec(code, {"__name__": "__main__", "__file__": path})
    except _CollectStop:
        pass
    except Exception as e:  # one bad page shouldn't abort the report
        import pandas as pd
        pdf_export.collect_table(pd.DataFrame({"note": [f"Page error: {e}"]}), caption=title)
    s = pdf_export._state()
    return (title, list(s["figs"]), list(s["tables"]))


def export_all_pages(specs: List[Tuple[str, str]], report_title: str = "QC Report",
                     progress=None) -> bytes:
    """Render every page in `specs` headlessly and return one combined PDF."""
    import streamlit as S

    out_fns = ["title", "header", "subheader", "caption", "markdown", "text", "write",
               "latex", "code", "divider", "metric", "dataframe", "table", "json",
               "image", "pyplot", "plotly_chart", "altair_chart", "success", "info",
               "warning", "error", "exception", "toast", "badge", "page_link",
               "download_button", "button"]
    box_fns = ["container", "expander", "popover", "empty", "form", "spinner", "status"]
    widget_defaults = {"selectbox": None, "multiselect": [], "radio": None,
                       "checkbox": False, "slider": None, "date_input": None,
                       "text_input": "", "number_input": 0, "file_uploader": None,
                       "color_picker": "", "time_input": None, "text_area": ""}
    saved = {n: getattr(S, n, None) for n in
             out_fns + box_fns + ["columns", "tabs", "sidebar", "stop"] + list(widget_defaults)}

    def noop(*a, **k): return None
    def cols(spec=1, *a, **k):
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        return [_Dummy() for _ in range(n)]
    def do_stop(*a, **k): raise _CollectStop()

    try:
        for n in out_fns:
            setattr(S, n, noop)
        for n in box_fns:
            setattr(S, n, lambda *a, **k: _Dummy())
        S.columns = cols
        S.tabs = lambda labels, *a, **k: [_Dummy() for _ in labels]
        S.sidebar = _Dummy()
        S.stop = do_stop
        for n, d in widget_defaults.items():
            setattr(S, n, (lambda dv: (lambda *a, **k: dv))(d))

        pdf_export.COLLECT_ONLY = True
        pages = []
        for i, (rel, title) in enumerate(specs, 1):
            pages.append(_run_page_collect(rel, title))
            if progress is not None:
                try:
                    progress(i / len(specs), title)
                except Exception:
                    pass
        return pdf_export.build_full_pdf(pages, report_title)
    finally:
        pdf_export.COLLECT_ONLY = False
        for n, v in saved.items():
            if v is not None:
                setattr(S, n, v)
