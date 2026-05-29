"""Light data-model helpers — join keys, derived columns, common views."""
from __future__ import annotations
from typing import Optional
import pandas as pd
import streamlit as st

from .data_loader import get_store
from . import transform as _tf


def ensure_enriched():
    """Derive PowerBI calculated columns if a page is hit before the main
    sidebar ran enrichment (Streamlit runs each page as its own script)."""
    _tf.enrich_store(get_store())


def _first_date_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["Prod Date", "ProdDate", "EcoDate", "Eco Date", "Date"]:
        if c in df.columns: return c
    for c in df.columns:
        if "date" in c.lower(): return c
    return None


def add_year(df: pd.DataFrame, date_col: str, year_col: str = "Year") -> pd.DataFrame:
    if date_col not in df.columns: return df
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out[year_col] = out[date_col].dt.year
    return out


def get_lse_info() -> Optional[pd.DataFrame]:
    return get_store().get("LseInfo")


def get_lse_eco(joined: bool = True) -> Optional[pd.DataFrame]:
    """LseEco. If joined=True, left-joins LseInfo on Lse_Id and derives Prod Date / Year."""
    ensure_enriched()
    store = get_store()
    eco = store.get("LseEco")
    if eco is None or eco.empty: return None
    info = store.get("LseInfo")
    if joined and info is not None and "Lse_Id" in eco.columns and "Lse_Id" in info.columns:
        info_cols = [c for c in ["Lse_Id", "LSE_NAME", "RsvCat", "OPER", "County", "WrkInt", "RevInt"] if c in info.columns]
        eco = eco.merge(info[info_cols], on="Lse_Id", how="left", suffixes=("", "_info"))
    dcol = _first_date_col(eco)
    if dcol:
        eco["Prod Date"] = pd.to_datetime(eco[dcol], errors="coerce")
        eco["Year"] = eco["Prod Date"].dt.year
    return eco


def get_mon_info(joined: bool = True) -> Optional[pd.DataFrame]:
    ensure_enriched()
    store = get_store()
    mon = store.get("MonInfo")
    if mon is None or mon.empty: return None
    info = store.get("LseInfo")
    if joined and info is not None and "Lse_Id" in mon.columns and "Lse_Id" in info.columns:
        info_cols = [c for c in ["Lse_Id", "LSE_NAME", "RsvCat", "OPER", "County"] if c in info.columns]
        mon = mon.merge(info[info_cols], on="Lse_Id", how="left", suffixes=("", "_info"))
    dcol = _first_date_col(mon)
    if dcol:
        mon["Prod Date"] = pd.to_datetime(mon[dcol], errors="coerce")
        mon["Year"] = mon["Prod Date"].dt.year
    return mon


def get_well_headers() -> Optional[pd.DataFrame]:
    return get_store().get("well_headers")


def get_los_long() -> Optional[pd.DataFrame]:
    store = get_store()
    los = store.get("los_long")
    if los is None:
        los = store.get("PowerBI_Long")
    return los


def lse_eco_columns() -> list[str]:
    eco = get_store().get("LseEco")
    return list(eco.columns) if eco is not None else []


def normalize_api(series: pd.Series) -> pd.Series:
    """Reduce any API (10/12/14-digit, with or without dashes) to a 10-digit
    API10 string, for joining well headers to PHDWin/Aries property tables."""
    digits = series.astype(str).str.replace(r"\D", "", regex=True)
    return digits.str.slice(0, 10).where(digits.str.len() >= 10, digits)

