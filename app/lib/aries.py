"""Source-aware accessors for the Aries QC report.

Aries tables live under st.session_state['store']['__aries__'] (loaded raw, then
enriched by aries_transform). These helpers normalize a per-lease "property"
lookup (PROPNUM -> RsvCat / LEASE_NAME / OPERATOR / COUNTY / lat / lon) and join
it onto AC_ONELINE / AC_MONTHLY / AC_PRODUCT so the pages can group by the same
dimensions the PowerBI report uses.
"""
from __future__ import annotations
from typing import List, Optional
import pandas as pd
import streamlit as st

from . import aries_transform as at


def _aries() -> dict:
    return st.session_state.get("store", {}).get("__aries__") or {}


def ensure_enriched():
    at.enrich_aries_store(st.session_state.get("store", {}))


def has_aries() -> bool:
    a = _aries()
    return bool(a) and "AC_ONELINE" in a and "AC_MONTHLY" in a


# Role -> ordered list of candidate AC_PROPERTY source columns. The reserve
# category and lease-name columns vary by client setup (SIPC_RSV_CAT vs
# SE_RSV_CAT vs RESCAT; LEASE_NAME vs LEASE), so resolve them by first match.
_PROP_ROLES = {
    "PROPNUM": ["PROPNUM"],
    "LSE_NAME": ["LEASE_NAME", "LEASE"],
    "OPER": ["OPERATOR"],
    "County": ["COUNTY"],
    "RsvCat": ["SIPC_RSV_CAT", "SE_RSV_CAT", "RESCAT", "RSV_CAT"],
    "API": ["API", "API10", "API14", "UWI"],
    "Latitude": ["LATITUDE", "S_LAT"],
    "Longitude": ["LONGITUDE", "S_LON"],
    "WI": ["WI"],
    "NRI": ["NRI"],
}


def get_property() -> Optional[pd.DataFrame]:
    a = _aries()
    prop = a.get("AC_PROPERTY")
    if prop is None or prop.empty:
        return None
    rename = {}
    for role, cands in _PROP_ROLES.items():
        src = next((c for c in cands if c in prop.columns), None)
        if src is not None and src not in rename:
            rename[src] = role
    out = prop[list(rename)].rename(columns=rename)
    return out


def _join_property(df: pd.DataFrame) -> pd.DataFrame:
    prop = get_property()
    if prop is not None and "PROPNUM" in df.columns and "PROPNUM" in prop.columns:
        df = df.merge(prop, on="PROPNUM", how="left", suffixes=("", "_p"))
    return df


def rsvcat_options() -> List[str]:
    prop = get_property()
    if prop is None or "RsvCat" not in prop.columns:
        return []
    return sorted([c for c in prop["RsvCat"].dropna().unique().tolist()])


def get_oneline() -> Optional[pd.DataFrame]:
    ensure_enriched()
    a = _aries()
    one = a.get("AC_ONELINE")
    if one is None or one.empty:
        return None
    return _join_property(one)


def get_monthly() -> Optional[pd.DataFrame]:
    ensure_enriched()
    a = _aries()
    mon = a.get("AC_MONTHLY")
    if mon is None or mon.empty:
        return None
    return _join_property(mon)


def monthly_guard(st) -> Optional[pd.DataFrame]:
    """Return enriched AC_MONTHLY, or render an accurate stop-message.

    Distinguishes "no Aries database loaded" from "AC_MONTHLY is present but
    empty" — the latter happens when the export was taken before an Aries
    monthly economic run, so the forecast/cash-flow stream isn't in the file.
    """
    a = _aries()
    if not a:
        st.warning("Upload an Aries database in the sidebar."); st.stop()
    mon = get_monthly()
    if mon is None:
        rows = 0 if a.get("AC_MONTHLY") is None else len(a["AC_MONTHLY"])
        st.warning(
            "`AC_MONTHLY` is empty in this Aries export, so the monthly "
            "forecast/economics charts can't be drawn. Re-export the database "
            "after running Aries economics with **monthly output** enabled "
            "(the reserves, PV, oneline and historical-production pages still "
            f"work from AC_ONELINE / AC_PRODUCT). [AC_MONTHLY rows: {rows}]"
        )
        st.stop()
    return mon


def get_product() -> Optional[pd.DataFrame]:
    ensure_enriched()
    a = _aries()
    prod = a.get("AC_PRODUCT")
    if prod is None or prod.empty:
        return None
    return _join_property(prod)


def apply_rsvcat(df: pd.DataFrame, selected: List[str]) -> pd.DataFrame:
    if not selected or df is None or "RsvCat" not in df.columns:
        return df
    return df[df["RsvCat"].isin(selected)]
