"""Per-page PDF export.

While a page renders, the chart helpers in `lib/charts.py` call `collect_fig`
and `collect_table` to push every figure and table they draw into a session
registry. After the page renders, `build_pdf()` assembles a single PDF
containing the page title, the active filter state (scenario / reserve
category / date anchor), and the collected charts and tables, exactly as
the user sees them.
"""
from __future__ import annotations
import io
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# When True, chart helpers collect figures/tables but skip live st.* rendering
# and the per-plot Options popover. Used by the "export all pages" run.
COLLECT_ONLY = False


def _state() -> Dict[str, Any]:
    return st.session_state.setdefault(
        "_pdf", {"figs": [], "tables": [], "title": ""}
    )


def reset(title: str = "") -> None:
    """Start a fresh registry. Call once per page render (in app.py main)."""
    st.session_state["_pdf"] = {"figs": [], "tables": [], "title": title}


def collect_fig(fig) -> None:
    _state()["figs"].append(fig)


def collect_table(df: pd.DataFrame, *, money_cols=(), int_cols=(), caption: str = "") -> None:
    _state()["tables"].append({
        "df": df.copy() if df is not None else pd.DataFrame(),
        "money_cols": list(money_cols),
        "int_cols": list(int_cols),
        "caption": caption,
    })


def is_empty() -> bool:
    s = _state()
    return not (s["figs"] or s["tables"])


def _filter_meta() -> str:
    parts: List[str] = []
    scn = st.session_state.get("aries_scenarios")
    if scn:
        parts.append(f"Scenario(s): {', '.join(map(str, scn))}")
        if len(scn) > 1:
            parts.append(f"View: {st.session_state.get('aries_scn_mode', 'Overlay')}")
    arsv = st.session_state.get("aries_rsvcat_selection")
    prsv = st.session_state.get("rsvcat_selection")
    rsv = arsv if arsv else prsv
    if rsv:
        parts.append(f"Reserve category: {', '.join(map(str, rsv))}")
    rng = st.session_state.get("chart_date_range")
    if rng and len(rng) == 2:
        parts.append(f"Date range: {rng[0]} → {rng[1]}")
    return "  •  ".join(parts)


_DEFAULT_PLOTLY_BLUES = {"#1f77b4", "#636efa", "rgb(31,119,180)", "rgb(99,110,250)"}
# Streamlit's "streamlit" template colorway placeholders that render near-black.
_SENTINELS = {f"#{i:06X}" for i in range(1, 11)} | {f"#{i:06x}" for i in range(1, 11)}
_SENTINEL_FALLBACK = px_colors = [
    "#636efa", "#EF553B", "#00cc96", "#ab63fa", "#FFA15A",
    "#19d3f3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]


def _fix_color(val, idx):
    """Replace a sentinel/blank color with a real palette color by index."""
    if val is None:
        return None
    if isinstance(val, str) and val in _SENTINELS:
        return _SENTINEL_FALLBACK[idx % len(_SENTINEL_FALLBACK)]
    if isinstance(val, (list, tuple)):
        return [_SENTINEL_FALLBACK[i % len(_SENTINEL_FALLBACK)] if (isinstance(v, str) and v in _SENTINELS) else v
                for i, v in enumerate(val)]
    return val


def _prepare_export_fig(fig):
    """Copy `fig`, normalize for static export, and force readable colors.

    Two problems Kaleido hits versus the in-app render:
    1. Streamlit's default template uses sentinel colorway placeholders
       (#000001..) the browser swaps client-side; statically they're black.
    2. Some traces have no explicit color and fall back to a default blue.

    Remap any sentinel colors to a real palette, pin phase colors for traces
    whose name maps to Oil/Gas/NGL/Boe, and force a white background.
    """
    try:
        from . import charts as _ch
    except Exception:
        _ch = None
    f = type(fig)(fig.to_plotly_json())  # deep-ish copy via JSON round-trip
    f.update_layout(template="plotly_white", paper_bgcolor="white", plot_bgcolor="white")
    for i, tr in enumerate(f.data):
        pc = _ch.phase_color(getattr(tr, "name", "") or "") if _ch else None
        # marker color — some trace types (box, histogram) don't expose .color
        marker = getattr(tr, "marker", None)
        if marker is not None and hasattr(type(marker), "color"):
            try:
                mk = _fix_color(marker.color, i)
                if pc and (mk is None or (isinstance(mk, str) and (mk == "" or mk in _DEFAULT_PLOTLY_BLUES))):
                    mk = pc
                if mk is not None:
                    marker.color = mk
            except (AttributeError, ValueError):
                pass
        # line color
        line = getattr(tr, "line", None)
        if line is not None and hasattr(type(line), "color"):
            try:
                ln = _fix_color(line.color, i)
                if pc and (ln is None or (isinstance(ln, str) and ln in _DEFAULT_PLOTLY_BLUES)):
                    ln = pc
                if ln is not None:
                    line.color = ln
            except (AttributeError, ValueError):
                pass
    return f


def _page_flowables(title, figs, tables, styles, *, heading_style="Heading1"):
    """ReportLab flowables for one page's title, figures and tables."""
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    flow = []
    if title:
        flow.append(Paragraph(title, styles[heading_style]))
        flow.append(Spacer(1, 0.1 * inch))
    for fig in figs:
        try:
            export_fig = _prepare_export_fig(fig)
            png = export_fig.to_image(format="png", width=1400, height=750, scale=2)
        except Exception as e:
            flow.append(Paragraph(f"<i>Chart render failed: {e}</i>", styles["Normal"]))
            continue
        flow.append(Image(io.BytesIO(png), width=9.5 * inch, height=5.0 * inch))
        flow.append(Spacer(1, 0.15 * inch))
    for t in tables:
        df: pd.DataFrame = t["df"]
        if df is None or df.empty:
            continue
        if t.get("caption"):
            flow.append(Paragraph(f"<b>{t['caption']}</b>", styles["Normal"]))
        show = df.copy()
        for c in t.get("money_cols", []):
            if c in show.columns:
                show[c] = show[c].map(lambda v: "" if pd.isna(v) else f"${v:,.0f}")
        for c in t.get("int_cols", []):
            if c in show.columns:
                show[c] = show[c].map(lambda v: "" if pd.isna(v) else f"{v:,.0f}")
        data = [list(show.columns)] + show.astype(str).values.tolist()
        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        flow.append(tbl)
        flow.append(Spacer(1, 0.15 * inch))
    return flow


def build_pdf() -> bytes:
    """Assemble the current page's collected figures/tables into a PDF."""
    from reportlab.lib.pagesizes import LETTER, landscape
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    s = _state()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(LETTER),
        leftMargin=0.4 * inch, rightMargin=0.4 * inch,
        topMargin=0.4 * inch, bottomMargin=0.4 * inch,
        title=s["title"] or "QC Report",
    )
    styles = getSampleStyleSheet()
    flow = []
    if s["title"]:
        flow.append(Paragraph(s["title"], styles["Title"]))
    meta = _filter_meta()
    if meta:
        flow.append(Paragraph(meta, styles["Normal"]))
        flow.append(Spacer(1, 0.15 * inch))
    flow += _page_flowables(None, s["figs"], s["tables"], styles)
    if not flow:
        flow.append(Paragraph("No charts or tables were rendered on this page.", styles["Normal"]))
    doc.build(flow)
    return buf.getvalue()


def build_full_pdf(pages: List[Tuple[str, list, list]], report_title: str = "QC Report") -> bytes:
    """Assemble a multi-page report: one section per (title, figs, tables)."""
    from reportlab.lib.pagesizes import LETTER, landscape
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(LETTER),
        leftMargin=0.4 * inch, rightMargin=0.4 * inch,
        topMargin=0.4 * inch, bottomMargin=0.4 * inch,
        title=report_title,
    )
    styles = getSampleStyleSheet()
    flow = [Paragraph(report_title, styles["Title"])]
    meta = _filter_meta()
    if meta:
        flow.append(Paragraph(meta, styles["Normal"]))
    flow.append(Spacer(1, 0.2 * inch))
    # Table of contents
    flow.append(Paragraph("<b>Contents</b>", styles["Heading2"]))
    for i, (title, _, _) in enumerate(pages, 1):
        flow.append(Paragraph(f"{i}. {title}", styles["Normal"]))
    flow.append(PageBreak())

    for title, figs, tables in pages:
        flow += _page_flowables(title, figs, tables, styles)
        flow.append(PageBreak())

    doc.build(flow)
    return buf.getvalue()


def safe_filename(title: str) -> str:
    import re
    base = re.sub(r"[^\w\-]+", "_", title or "QC_report").strip("_")
    return f"{base or 'QC_report'}.pdf"
