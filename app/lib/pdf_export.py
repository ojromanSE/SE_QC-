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
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


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


def build_pdf() -> bytes:
    """Assemble the collected figures and tables into a PDF, in render order."""
    from reportlab.lib.pagesizes import LETTER, landscape
    from reportlab.lib.units import inch
    from reportlab.platypus import (SimpleDocTemplate, Image, Paragraph, Spacer,
                                    Table, TableStyle, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

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

    img_w = 9.5 * inch  # landscape Letter - margins
    img_h = 5.0 * inch

    for fig in s["figs"]:
        try:
            png = fig.to_image(format="png", width=1400, height=750, scale=2)
        except Exception as e:
            flow.append(Paragraph(f"<i>Chart render failed: {e}</i>", styles["Normal"]))
            continue
        flow.append(Image(io.BytesIO(png), width=img_w, height=img_h))
        flow.append(Spacer(1, 0.15 * inch))

    for t in s["tables"]:
        df: pd.DataFrame = t["df"]
        if df is None or df.empty:
            continue
        if t["caption"]:
            flow.append(Paragraph(f"<b>{t['caption']}</b>", styles["Normal"]))
        show = df.copy()
        for c in t["money_cols"]:
            if c in show.columns:
                show[c] = show[c].map(lambda v: "" if pd.isna(v) else f"${v:,.0f}")
        for c in t["int_cols"]:
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

    if not flow:
        flow.append(Paragraph("No charts or tables were rendered on this page.", styles["Normal"]))

    doc.build(flow)
    return buf.getvalue()


def safe_filename(title: str) -> str:
    import re
    base = re.sub(r"[^\w\-]+", "_", title or "QC_report").strip("_")
    return f"{base or 'QC_report'}.pdf"
