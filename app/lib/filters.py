"""Sidebar slicers that mirror the PowerBI page-level filter (RsvCat)."""
from __future__ import annotations
from typing import List
import pandas as pd
import streamlit as st


def rsvcat_filter(default: List[str] | None = None) -> List[str]:
    store = st.session_state.get("store", {})
    lse = store.get("LseInfo")
    if lse is None or "RsvCat" not in lse.columns:
        return []
    cats = sorted([c for c in lse["RsvCat"].dropna().unique().tolist()])
    if not cats:
        return []
    if "rsvcat_selection" not in st.session_state:
        st.session_state["rsvcat_selection"] = default if default else cats
    return st.sidebar.multiselect(
        "Reserve Category (RsvCat)",
        options=cats,
        default=st.session_state["rsvcat_selection"],
        key="rsvcat_selection",
    )


def apply_rsvcat(df: pd.DataFrame, selected: List[str], lse_info: pd.DataFrame | None = None) -> pd.DataFrame:
    """Filter `df` rows whose Lse_Id matches LseInfo rows in selected RsvCat."""
    if not selected:
        return df
    if "RsvCat" in df.columns:
        return df[df["RsvCat"].isin(selected)]
    if lse_info is not None and "Lse_Id" in df.columns and "Lse_Id" in lse_info.columns:
        keep = lse_info.loc[lse_info["RsvCat"].isin(selected), "Lse_Id"].unique()
        return df[df["Lse_Id"].isin(keep)]
    return df
