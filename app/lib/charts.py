"""Plotly chart helpers that replicate the PowerBI visuals used in the report."""
from __future__ import annotations
import re
from typing import Iterable, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from . import pdf_export


def _render(fig, *, key: Optional[str] = None):
    """Render a Plotly figure and also push it into the PDF registry."""
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, **({"key": key} if key else {}))


PALETTE = px.colors.qualitative.Plotly


# --- global defaults (set from the sidebar in app.py) ----------------------
def yaxis_type() -> str:
    """Default 'log'/'linear' from the sidebar; per-plot controls can override."""
    return "log" if st.session_state.get("chart_yscale") == "log" else "linear"


def _global_range():
    rng = st.session_state.get("chart_date_range")
    return rng if rng and len(rng) == 2 else None


def filter_dates(df: pd.DataFrame, xcol: str) -> pd.DataFrame:
    """Clip on the sidebar's global date range (used by inline page charts)."""
    return _clip(df, xcol, _global_range())


def _ckey(key: str, title: str) -> str:
    return re.sub(r"\W+", "_", (key or title or "plot")).strip("_") or "plot"


def _clip(df: pd.DataFrame, xcol: str, rng) -> pd.DataFrame:
    """Clip df on xcol to rng. Handles datetime ranges and integer Year ranges."""
    if not rng or len(rng) != 2 or xcol is None or xcol not in df.columns:
        return df
    lo, hi = rng
    col = df[xcol]
    if pd.api.types.is_datetime64_any_dtype(col):
        return df[(col >= pd.Timestamp(lo)) & (col <= pd.Timestamp(hi))]
    if pd.api.types.is_numeric_dtype(col):
        lo = lo.year if hasattr(lo, "year") else int(lo)
        hi = hi.year if hasattr(hi, "year") else int(hi)
        return df[(col >= lo) & (col <= hi)]
    return df


def _plot_controls(ckey, *, df=None, date_col=None, series_values=None, series_label="Series"):
    """Per-plot Options popover: y-axis scale, date range, and (for by-lease
    plots) a lease multiselect + roll-up toggle. Seeds from the sidebar globals.
    Returns dict(scale, range, series, rollup).
    """
    res = {"scale": yaxis_type(), "range": _global_range(), "series": None, "rollup": False}
    with st.popover("Options", use_container_width=False):
        sc = st.radio("Y-axis scale", ["Linear", "Log"], horizontal=True,
                      index=1 if res["scale"] == "log" else 0, key=f"{ckey}_scale")
        res["scale"] = "log" if sc == "Log" else "linear"

        if df is not None and date_col and date_col in df.columns:
            col = df[date_col].dropna()
            if pd.api.types.is_datetime64_any_dtype(col) and not col.empty:
                lo, hi = col.min().date(), col.max().date()
                if lo < hi:
                    dr = st.date_input("Date range", (lo, hi), min_value=lo, max_value=hi, key=f"{ckey}_dr")
                    if isinstance(dr, (list, tuple)) and len(dr) == 2:
                        res["range"] = dr
            elif pd.api.types.is_numeric_dtype(col) and not col.empty:
                lo, hi = int(col.min()), int(col.max())
                if lo < hi:
                    res["range"] = st.slider("Year range", lo, hi, (lo, hi), key=f"{ckey}_yr")

        if series_values:
            res["rollup"] = st.checkbox("Roll up (combine all)", value=False, key=f"{ckey}_rollup")
            if not res["rollup"]:
                res["series"] = st.multiselect(series_label or "Series", series_values,
                                               default=series_values, key=f"{ckey}_series")
    return res


def _scn_state(df):
    """Multi-scenario context for a frame carrying a SCENARIO column.

    Returns (scenarios, mode) when >1 selected scenario is present, else
    (None, None). `mode` is 'Overlay' or 'Split' from the sidebar.
    """
    sel = st.session_state.get("aries_scenarios") or []
    if df is None or "SCENARIO" not in getattr(df, "columns", []):
        return None, None
    present = [s for s in sel if s in set(df["SCENARIO"].astype(str).unique())]
    if len(present) <= 1:
        return None, None
    return present, st.session_state.get("aries_scn_mode", "Overlay")


def _split_panels(render_one, df, scns, base_key, title):
    """Render `render_one(sub_df, key, title)` once per scenario in columns."""
    cols = st.columns(len(scns))
    for c, s in zip(cols, scns):
        with c:
            st.markdown(f"**{s}**")
            render_one(df[df["SCENARIO"].astype(str) == s], f"{base_key}_{s}", f"{title} — {s}")


def available_pv_columns(df: pd.DataFrame) -> List[str]:
    """PV columns present in a frame (e.g. 'PV10 ($)'), ordered by discount rate."""
    if df is None:
        return []
    pvs = [c for c in df.columns if re.fullmatch(r"PV\d+ \(\$\)", str(c))]
    return sorted(pvs, key=lambda c: int(re.search(r"PV(\d+)", c).group(1)))


def pv_select(df: pd.DataFrame, key: str, default: str = "PV10 ($)", label: str = "PV measure") -> Optional[str]:
    """Per-page PV picker. Lists the PV columns actually present in `df` and
    returns the chosen one (default PV10 when available). Returns None if the
    frame has no PV columns."""
    opts = available_pv_columns(df)
    if not opts:
        return None
    idx = opts.index(default) if default in opts else 0
    return st.selectbox(label, opts, index=idx, key=f"pv_{key}")


def fmt_int(s: pd.Series) -> pd.Series:
    return s.map(lambda v: "" if pd.isna(v) else f"{v:,.0f}")


def fmt_money(s: pd.Series) -> pd.Series:
    return s.map(lambda v: "" if pd.isna(v) else f"${v:,.0f}")


def show_table(df: pd.DataFrame, *, money_cols: Iterable[str] = (), int_cols: Iterable[str] = (),
               height: int = 320, caption: str = ""):
    pdf_export.collect_table(df, money_cols=money_cols, int_cols=int_cols, caption=caption)
    show = df.copy()
    for c in money_cols:
        if c in show.columns: show[c] = fmt_money(show[c])
    for c in int_cols:
        if c in show.columns: show[c] = fmt_int(show[c])
    st.dataframe(show, height=height, use_container_width=True, hide_index=True)


def pie(df: pd.DataFrame, names: str, values: str, title: str = "", key: str = ""):
    if df.empty or names not in df.columns or values not in df.columns:
        st.info(f"No data for pie ({names} vs {values}).")
        return
    ck = _ckey(key, title)
    scns, _ = _scn_state(df)
    if scns:
        _split_panels(lambda d, k, t: pie(d, names, values, t, k), df, scns, ck, title); return
    g = df.groupby(names, dropna=False)[values].sum().reset_index()
    fig = px.pie(g, names=names, values=values, title=title, hole=0.0)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def grouped_column(df: pd.DataFrame, x: str, ys: List[str], title: str = "", barmode: str = "group", key: str = ""):
    if df.empty:
        st.info("No data."); return
    cols = [c for c in ys if c in df.columns]
    if not cols:
        st.info(f"Columns not found: {ys}"); return
    ck = _ckey(key, title)
    scns, _ = _scn_state(df)
    if scns:  # multi-scenario: one panel per scenario (overlay of multi-bar is unreadable)
        _split_panels(lambda d, k, t: grouped_column(d, x, ys, t, barmode, k), df, scns, ck, title); return
    ctrl = _plot_controls(ck, df=df, date_col=x)
    df = _clip(df, x, ctrl["range"])
    g = df.groupby(x, dropna=False)[cols].sum().reset_index().sort_values(x)
    fig = go.Figure()
    for i, c in enumerate(cols):
        fig.add_bar(x=g[x], y=g[c], name=c, marker_color=PALETTE[i % len(PALETTE)])
    fig.update_layout(title=title, barmode=barmode, xaxis_title=x, legend_title="")
    fig.update_yaxes(type=ctrl["scale"])
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def stacked_column(df: pd.DataFrame, x: str, y: str, color: str, title: str = "", key: str = ""):
    if df.empty or any(c not in df.columns for c in [x, y, color]):
        st.info("No data."); return
    ck = _ckey(key, title)
    scns, _ = _scn_state(df)
    if scns:
        _split_panels(lambda d, k, t: stacked_column(d, x, y, color, t, k), df, scns, ck, title); return
    ctrl = _plot_controls(ck, df=df, date_col=x)
    df = _clip(df, x, ctrl["range"])
    g = df.groupby([x, color], dropna=False)[y].sum().reset_index().sort_values(x)
    fig = px.bar(g, x=x, y=y, color=color, title=title)
    fig.update_layout(barmode="stack")
    fig.update_yaxes(type=ctrl["scale"])
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def line(df: pd.DataFrame, x: str, y: str, color: Optional[str] = None, title: str = "", key: str = ""):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info("No data."); return
    ck = _ckey(key, title)
    scns, mode = _scn_state(df)
    if scns and mode == "Split":
        _split_panels(lambda d, k, t: line(d, x, y, color, t, k), df, scns, ck, title); return
    overlay = bool(scns)  # Overlay mode with >1 scenario
    has_series = bool(color and color in df.columns)
    svals = sorted(df[color].dropna().astype(str).unique().tolist()) if has_series else None
    ctrl = _plot_controls(ck, df=df, date_col=x, series_values=svals, series_label=color)
    df = _clip(df, x, ctrl["range"])
    use_color = color if has_series else None
    if has_series:
        if ctrl["rollup"]:
            use_color = None
        elif ctrl["series"] is not None:
            df = df[df[color].astype(str).isin(ctrl["series"])]
    # In overlay mode, scenario becomes a series: color if no lease series, else line dash.
    dash = None
    if overlay:
        if use_color:
            dash = "SCENARIO"
        else:
            use_color = "SCENARIO"
    by = [x] + ([use_color] if use_color else []) + ([dash] if dash else [])
    g = df.groupby(by, dropna=False)[y].sum().reset_index().sort_values(x)
    fig = px.line(g, x=x, y=y, color=use_color, line_dash=dash, title=title)
    fig.update_yaxes(type=ctrl["scale"])
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def weighted_line(df: pd.DataFrame, x: str, num: str, den: str, title: str = "", key: str = ""):
    """Line of a volume-weighted ratio = sum(num) / sum(den) per x.

    Use for realized prices and other per-unit metrics where summing the raw
    per-row ratio would be wrong (a price is Σrevenue / Σvolume, not Σprice).
    Supports scenario overlay/split and the per-plot scale/date controls.
    """
    if df.empty or x not in df.columns or num not in df.columns or den not in df.columns:
        st.info("No data."); return
    ck = _ckey(key, title)
    scns, mode = _scn_state(df)
    if scns and mode == "Split":
        _split_panels(lambda d, k, t: weighted_line(d, x, num, den, t, k), df, scns, ck, title); return
    overlay = bool(scns)
    ctrl = _plot_controls(ck, df=df, date_col=x)
    df = _clip(df, x, ctrl["range"])
    by = [x] + (["SCENARIO"] if overlay else [])
    g = df.groupby(by, dropna=False)[[num, den]].sum().reset_index()
    g["__ratio"] = g[num] / g[den].replace(0, pd.NA)
    g = g.dropna(subset=["__ratio"]).sort_values(x)
    fig = px.line(g, x=x, y="__ratio", color="SCENARIO" if overlay else None, title=title)
    fig.update_yaxes(type=ctrl["scale"])
    fig.update_layout(yaxis_title=title or "Realized price")
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def combo_revenue_opex_cf(df: pd.DataFrame, x: str, bar_ys: List[str], line_y: str, title: str = "", key: str = ""):
    """Cash-Flow page: stacked bars for components, line for BFIT CF on secondary axis."""
    cols = [c for c in bar_ys if c in df.columns] + ([line_y] if line_y in df.columns else [])
    if df.empty or not cols:
        st.info("No data."); return
    ck = _ckey(key, title)
    scns, _ = _scn_state(df)
    if scns:
        _split_panels(lambda d, k, t: combo_revenue_opex_cf(d, x, bar_ys, line_y, t, k), df, scns, ck, title); return
    ctrl = _plot_controls(ck, df=df, date_col=x)
    df = _clip(df, x, ctrl["range"])
    g = df.groupby(x, dropna=False)[cols].sum().reset_index().sort_values(x)
    fig = go.Figure()
    for i, c in enumerate([c for c in bar_ys if c in g.columns]):
        fig.add_bar(x=g[x], y=g[c], name=c, marker_color=PALETTE[i % len(PALETTE)])
    if line_y in g.columns:
        fig.add_trace(go.Scatter(x=g[x], y=g[line_y], name=line_y, mode="lines+markers",
                                 yaxis="y2", line=dict(color="#d62728", width=3)))
    log = ctrl["scale"] == "log"
    fig.update_layout(
        title=title, barmode="relative",
        yaxis=dict(title="Components ($)", type="log" if log else "linear"),
        yaxis2=dict(title=line_y, overlaying="y", side="right", type="log" if log else "linear"),
        legend=dict(orientation="h", y=-0.2),
    )
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def treemap(df: pd.DataFrame, path: List[str], values: str, title: str = "", key: str = ""):
    if df.empty or values not in df.columns:
        st.info("No data."); return
    cols = [p for p in path if p in df.columns]
    if not cols:
        st.info("No grouping cols."); return
    ck = _ckey(key, title)
    scns, _ = _scn_state(df)
    if scns:
        _split_panels(lambda dd, k, t: treemap(dd, path, values, t, k), df, scns, ck, title); return
    d = df.copy()
    for c in cols:  # treemaps reject null/blank path labels
        d[c] = d[c].fillna("(blank)").replace("", "(blank)")
    g = d.groupby(cols, dropna=False)[values].sum().reset_index()
    g = g[g[values] > 0]
    if g.empty:
        st.info("No positive values."); return
    fig = px.treemap(g, path=cols, values=values, title=title)
    fig.update_traces(textinfo="label+value+percent parent")
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def box_by_group(df: pd.DataFrame, group: str, value: str, sample: Optional[str] = None, title: str = "", key: str = ""):
    if df.empty or group not in df.columns or value not in df.columns:
        st.info("No data."); return
    ck = _ckey(key, title)
    scns, mode = _scn_state(df)
    if scns and mode == "Split":
        _split_panels(lambda d, k, t: box_by_group(d, group, value, sample, t, k), df, scns, ck, title); return
    ctrl = _plot_controls(ck, df=df, date_col=group)
    df = _clip(df, group, ctrl["range"])
    keep = [group, value] + ([sample] if sample and sample in df.columns else []) + (["SCENARIO"] if scns else [])
    d = df[keep].dropna(subset=[value])
    if d.empty:
        st.info("No data."); return
    fig = px.box(d, x=group, y=value, color="SCENARIO" if scns else None, points="outliers", title=title,
                 hover_data=[sample] if sample and sample in d.columns else None)
    fig.update_yaxes(type=ctrl["scale"])
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def histogram(df: pd.DataFrame, value: str, bins: int = 30, title: str = "", key: str = ""):
    if df.empty or value not in df.columns:
        st.info("No data."); return
    d = df[[value]].dropna()
    if d.empty:
        st.info("No data."); return
    ck = _ckey(key, title)
    ctrl = _plot_controls(ck)
    fig = px.histogram(d, x=value, nbins=bins, title=title)
    fig.update_yaxes(type=ctrl["scale"])  # log scale applies to the count (y) axis
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def scatter(df: pd.DataFrame, x: str, y: str, color: Optional[str] = None, hover: Optional[str] = None,
            title: str = "", key: str = ""):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info("No data."); return
    ck = _ckey(key, title)
    scns, mode = _scn_state(df)
    if scns and mode == "Split":
        _split_panels(lambda d, k, t: scatter(d, x, y, color, hover, t, k), df, scns, ck, title); return
    has_series = bool(color and color in df.columns)
    svals = sorted(df[color].dropna().astype(str).unique().tolist()) if has_series else None
    ctrl = _plot_controls(ck, series_values=svals, series_label=color)
    d = df
    use_color = color if has_series else None
    if has_series:
        if ctrl["rollup"]:
            use_color = None
        elif ctrl["series"] is not None:
            d = d[d[color].astype(str).isin(ctrl["series"])]
    symbol = "SCENARIO" if scns else None  # overlay: distinguish scenarios by marker symbol
    fig = px.scatter(d, x=x, y=y, color=use_color, symbol=symbol,
                     hover_name=hover if hover and hover in d.columns else None, title=title)
    fig.update_yaxes(type=ctrl["scale"])
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")


def _map_zoom(lat, lon):
    """Rough zoom level from coordinate span."""
    span = max((lat.max() - lat.min()), (lon.max() - lon.min()), 1e-4)
    import math
    return float(min(13, max(3, 8 - math.log2(span * 12 + 1))))


def well_map(df: pd.DataFrame, slat: str, slon: str, blat: Optional[str] = None, blon: Optional[str] = None,
             hover: Optional[str] = None, size: Optional[str] = None, title: str = "", key: str = ""):
    """Draw wells from well-header coordinates.

    Horizontal/deviated wells (a bottom-hole location that differs from the
    surface hole) are drawn as a line from surface to bottom hole; vertical
    wells are drawn as a point at the well head. Surface holes are always
    marked, optionally sized by `size` (e.g. PV10).
    """
    if df.empty or slat not in df.columns or slon not in df.columns:
        st.info("Map needs surface-hole latitude/longitude columns."); return
    d = df.dropna(subset=[slat, slon]).copy()
    if d.empty:
        st.info("No georeferenced wells."); return

    has_bh = bool(blat and blon and blat in d.columns and blon in d.columns)
    eps = 1e-6
    if has_bh:
        bh = pd.to_numeric(d[blat], errors="coerce")
        bo = pd.to_numeric(d[blon], errors="coerce")
        is_lat = bh.notna() & bo.notna() & ((bh - d[slat]).abs() + (bo - d[slon]).abs() > eps)
    else:
        is_lat = pd.Series(False, index=d.index)

    fig = go.Figure()

    # Lateral lines (one trace, segments separated by None)
    lat_lines, lon_lines = [], []
    for _, r in d[is_lat].iterrows():
        lat_lines += [r[slat], r[blat], None]
        lon_lines += [r[slon], r[blon], None]
    if lat_lines:
        fig.add_trace(go.Scattermapbox(lat=lat_lines, lon=lon_lines, mode="lines",
                                       line=dict(width=3, color="#d62728"),
                                       name="Lateral", hoverinfo="skip"))

    # Surface-hole markers
    hover_txt = d[hover].astype(str) if hover and hover in d.columns else None
    marker = dict(size=9, color="#1f77b4")
    if size and size in d.columns:
        s = pd.to_numeric(d[size], errors="coerce").abs()
        if s.notna().any() and s.max() and s.max() > 0:
            marker = dict(size=(s / s.max() * 26 + 7).fillna(7), color=s, colorscale="Viridis",
                          showscale=True, colorbar=dict(title=size))
    fig.add_trace(go.Scattermapbox(
        lat=d[slat], lon=d[slon], mode="markers", marker=marker,
        text=hover_txt, name="Well head",
        hovertemplate=("%{text}<br>" if hover_txt is not None else "") +
                      "%{lat:.4f}, %{lon:.4f}" +
                      (f"<br>{size}: %{{marker.color:,.0f}}" if isinstance(marker.get("color"), pd.Series) else "") +
                      "<extra></extra>",
    ))

    fig.update_layout(
        title=title, height=620, mapbox_style="open-street-map",
        mapbox=dict(center=dict(lat=float(d[slat].mean()), lon=float(d[slon].mean())),
                    zoom=_map_zoom(d[slat], d[slon])),
        margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="h", y=-0.05),
    )
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{_ckey(key, title)}_fig")


def los_tie_out_bars(long_df: pd.DataFrame, line_item: str, calc_df: pd.DataFrame, calc_date: str, calc_value: str,
                     title: str = "", key: str = ""):
    """Side-by-side bars: reported LOS vs model calculation, per Date."""
    a = long_df[long_df["Line Item"] == line_item][["Date", "Value"]].rename(columns={"Value": "Reported (LOS)"})
    a["Date"] = pd.to_datetime(a["Date"], errors="coerce")
    b = calc_df[[calc_date, calc_value]].rename(columns={calc_date: "Date", calc_value: "Calculated"})
    b["Date"] = pd.to_datetime(b["Date"], errors="coerce")
    a = a.groupby("Date", as_index=False)["Reported (LOS)"].sum()
    b = b.groupby("Date", as_index=False)["Calculated"].sum()
    m = pd.merge(a, b, on="Date", how="outer").sort_values("Date")
    ck = _ckey(key, title)
    ctrl = _plot_controls(ck, df=m, date_col="Date")
    m = _clip(m, "Date", ctrl["range"])
    if m.empty:
        st.info("No tie-out data."); return
    fig = go.Figure()
    fig.add_bar(x=m["Date"], y=m["Reported (LOS)"], name="Reported (LOS)", marker_color=PALETTE[0])
    fig.add_bar(x=m["Date"], y=m["Calculated"], name="Calculated", marker_color=PALETTE[1])
    fig.update_layout(title=title, barmode="group", xaxis_title="Date", legend=dict(orientation="h", y=-0.2))
    fig.update_yaxes(type=ctrl["scale"])
    pdf_export.collect_fig(fig)
    st.plotly_chart(fig, use_container_width=True, key=f"{ck}_fig")
