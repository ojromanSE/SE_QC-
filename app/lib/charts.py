"""Plotly chart helpers that replicate the PowerBI visuals used in the report."""
from __future__ import annotations
from typing import Iterable, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PALETTE = px.colors.qualitative.Plotly


# --- shared chart controls (set from the sidebar in app.py) ----------------
def yaxis_type() -> str:
    """'log' or 'linear' from the sidebar Y-axis scale toggle."""
    return "log" if st.session_state.get("chart_yscale") == "log" else "linear"


def filter_dates(df: pd.DataFrame, xcol: str) -> pd.DataFrame:
    """If a date range is anchored in the sidebar, clip `df` on its x column.

    Works for datetime x columns and integer Year columns.
    """
    rng = st.session_state.get("chart_date_range")
    if not rng or len(rng) != 2 or xcol not in df.columns:
        return df
    start, end = pd.Timestamp(rng[0]), pd.Timestamp(rng[1])
    col = df[xcol]
    if pd.api.types.is_datetime64_any_dtype(col):
        return df[(col >= start) & (col <= end)]
    if pd.api.types.is_numeric_dtype(col):
        return df[(col >= start.year) & (col <= end.year)]
    return df


def _apply_yscale(fig, axis: str = "y"):
    t = yaxis_type()
    if t == "log":
        (fig.update_yaxes if axis == "y" else fig.update_xaxes)(type="log")
    return fig


def fmt_int(s: pd.Series) -> pd.Series:
    return s.map(lambda v: "" if pd.isna(v) else f"{v:,.0f}")


def fmt_money(s: pd.Series) -> pd.Series:
    return s.map(lambda v: "" if pd.isna(v) else f"${v:,.0f}")


def show_table(df: pd.DataFrame, *, money_cols: Iterable[str] = (), int_cols: Iterable[str] = (), height: int = 320):
    show = df.copy()
    for c in money_cols:
        if c in show.columns: show[c] = fmt_money(show[c])
    for c in int_cols:
        if c in show.columns: show[c] = fmt_int(show[c])
    st.dataframe(show, height=height, use_container_width=True, hide_index=True)


def pie(df: pd.DataFrame, names: str, values: str, title: str = ""):
    if df.empty or names not in df.columns or values not in df.columns:
        st.info(f"No data for pie ({names} vs {values}).")
        return
    g = df.groupby(names, dropna=False)[values].sum().reset_index()
    fig = px.pie(g, names=names, values=values, title=title, hole=0.0)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)


def grouped_column(df: pd.DataFrame, x: str, ys: List[str], title: str = "", barmode: str = "group"):
    if df.empty:
        st.info("No data."); return
    cols = [c for c in ys if c in df.columns]
    if not cols:
        st.info(f"Columns not found: {ys}"); return
    df = filter_dates(df, x)
    g = df.groupby(x, dropna=False)[cols].sum().reset_index().sort_values(x)
    fig = go.Figure()
    for i, c in enumerate(cols):
        fig.add_bar(x=g[x], y=g[c], name=c, marker_color=PALETTE[i % len(PALETTE)])
    fig.update_layout(title=title, barmode=barmode, xaxis_title=x, legend_title="")
    _apply_yscale(fig)
    st.plotly_chart(fig, use_container_width=True)


def stacked_column(df: pd.DataFrame, x: str, y: str, color: str, title: str = ""):
    if df.empty or any(c not in df.columns for c in [x, y, color]):
        st.info("No data."); return
    df = filter_dates(df, x)
    g = df.groupby([x, color], dropna=False)[y].sum().reset_index().sort_values(x)
    fig = px.bar(g, x=x, y=y, color=color, title=title)
    fig.update_layout(barmode="stack")
    _apply_yscale(fig)
    st.plotly_chart(fig, use_container_width=True)


def line(df: pd.DataFrame, x: str, y: str, color: Optional[str] = None, title: str = ""):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info("No data."); return
    df = filter_dates(df, x)
    by = [x] + ([color] if color and color in df.columns else [])
    g = df.groupby(by, dropna=False)[y].sum().reset_index().sort_values(x)
    fig = px.line(g, x=x, y=y, color=color if color in (df.columns if color else []) else None, title=title)
    _apply_yscale(fig)
    st.plotly_chart(fig, use_container_width=True)


def combo_revenue_opex_cf(df: pd.DataFrame, x: str, bar_ys: List[str], line_y: str, title: str = ""):
    """Cash-Flow page: stacked bars for components, line for BFIT CF on secondary axis."""
    cols = [c for c in bar_ys if c in df.columns] + ([line_y] if line_y in df.columns else [])
    if df.empty or not cols:
        st.info("No data."); return
    df = filter_dates(df, x)
    g = df.groupby(x, dropna=False)[cols].sum().reset_index().sort_values(x)
    fig = go.Figure()
    for i, c in enumerate([c for c in bar_ys if c in g.columns]):
        fig.add_bar(x=g[x], y=g[c], name=c, marker_color=PALETTE[i % len(PALETTE)])
    if line_y in g.columns:
        fig.add_trace(go.Scatter(x=g[x], y=g[line_y], name=line_y, mode="lines+markers",
                                 yaxis="y2", line=dict(color="#d62728", width=3)))
    log = yaxis_type() == "log"
    fig.update_layout(
        title=title, barmode="relative",
        yaxis=dict(title="Components ($)", type="log" if log else "linear"),
        yaxis2=dict(title=line_y, overlaying="y", side="right", type="log" if log else "linear"),
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig, use_container_width=True)


def treemap(df: pd.DataFrame, path: List[str], values: str, title: str = ""):
    if df.empty or values not in df.columns:
        st.info("No data."); return
    cols = [p for p in path if p in df.columns]
    if not cols:
        st.info("No grouping cols."); return
    d = df.copy()
    for c in cols:  # treemaps reject null/blank path labels
        d[c] = d[c].fillna("(blank)").replace("", "(blank)")
    g = d.groupby(cols, dropna=False)[values].sum().reset_index()
    g = g[g[values] > 0]
    if g.empty:
        st.info("No positive values."); return
    fig = px.treemap(g, path=cols, values=values, title=title)
    fig.update_traces(textinfo="label+value+percent parent")
    st.plotly_chart(fig, use_container_width=True)


def box_by_group(df: pd.DataFrame, group: str, value: str, sample: Optional[str] = None, title: str = ""):
    if df.empty or group not in df.columns or value not in df.columns:
        st.info("No data."); return
    df = filter_dates(df, group)
    d = df[[group, value] + ([sample] if sample and sample in df.columns else [])].dropna(subset=[value])
    if d.empty:
        st.info("No data."); return
    fig = px.box(d, x=group, y=value, points="outliers", title=title,
                 hover_data=[sample] if sample and sample in d.columns else None)
    _apply_yscale(fig)
    st.plotly_chart(fig, use_container_width=True)


def histogram(df: pd.DataFrame, value: str, bins: int = 30, title: str = ""):
    if df.empty or value not in df.columns:
        st.info("No data."); return
    d = df[[value]].dropna()
    if d.empty:
        st.info("No data."); return
    fig = px.histogram(d, x=value, nbins=bins, title=title)
    _apply_yscale(fig)  # log scale applies to the count (y) axis
    st.plotly_chart(fig, use_container_width=True)


def scatter(df: pd.DataFrame, x: str, y: str, color: Optional[str] = None, hover: Optional[str] = None, title: str = ""):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info("No data."); return
    fig = px.scatter(df, x=x, y=y, color=color if color in df.columns else None,
                     hover_name=hover if hover and hover in df.columns else None, title=title)
    _apply_yscale(fig)
    st.plotly_chart(fig, use_container_width=True)


def well_map(df: pd.DataFrame, lat: str, lon: str, size: Optional[str] = None, hover: Optional[str] = None, title: str = ""):
    if df.empty or lat not in df.columns or lon not in df.columns:
        st.info("Map needs latitude/longitude columns."); return
    d = df.dropna(subset=[lat, lon]).copy()
    if d.empty:
        st.info("No georeferenced rows."); return
    s = None
    if size and size in d.columns:
        s = d[size].abs()
        if s.max() and s.max() > 0:
            s = (s / s.max()) * 40 + 5
    fig = px.scatter_mapbox(
        d, lat=lat, lon=lon, size=s if s is not None else None,
        hover_name=hover if hover and hover in d.columns else None,
        zoom=4, height=600, title=title,
    )
    fig.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)


def los_tie_out_bars(long_df: pd.DataFrame, line_item: str, calc_df: pd.DataFrame, calc_date: str, calc_value: str, title: str = ""):
    """Side-by-side bars: PowerBI_Long (uploaded LOS) vs LseEco calculation, per Date."""
    a = long_df[long_df["Line Item"] == line_item][["Date", "Value"]].rename(columns={"Value": "Reported (LOS)"})
    a["Date"] = pd.to_datetime(a["Date"], errors="coerce")
    b = calc_df[[calc_date, calc_value]].rename(columns={calc_date: "Date", calc_value: "Calculated"})
    b["Date"] = pd.to_datetime(b["Date"], errors="coerce")
    a = a.groupby("Date", as_index=False)["Reported (LOS)"].sum()
    b = b.groupby("Date", as_index=False)["Calculated"].sum()
    m = pd.merge(a, b, on="Date", how="outer").sort_values("Date")
    m = filter_dates(m, "Date")
    if m.empty:
        st.info("No tie-out data."); return
    fig = go.Figure()
    fig.add_bar(x=m["Date"], y=m["Reported (LOS)"], name="Reported (LOS)", marker_color=PALETTE[0])
    fig.add_bar(x=m["Date"], y=m["Calculated"], name="Calculated", marker_color=PALETTE[1])
    fig.update_layout(title=title, barmode="group", xaxis_title="Date", legend=dict(orientation="h", y=-0.2))
    _apply_yscale(fig)
    st.plotly_chart(fig, use_container_width=True)
