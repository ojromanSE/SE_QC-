"""Data ingestion for PHDWin .mdb, Aries .mdb, well-headers CSV and LOS tie-out xlsx.

Strategy on Streamlit Community Cloud (Linux): use the `mdbtools` package
(declared in packages.txt) via subprocess to dump tables out of `.mdb` files.
`.accdb` files don't work on Linux — the UI tells the user to pre-export.
"""
from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st


PHDWIN_TABLES = ["LseInfo", "LseEco", "MonInfo"]
ARIES_TABLES = ["AC_PROPERTY", "AC_ECONOMIC", "AC_ONELINE", "AC_PRODUCT", "AC_DAILY"]


def mdbtools_available() -> bool:
    return shutil.which("mdb-tables") is not None and shutil.which("mdb-export") is not None


def list_mdb_tables(mdb_path: Path) -> List[str]:
    out = subprocess.run(
        ["mdb-tables", "-1", str(mdb_path)],
        capture_output=True, text=True, check=True,
    )
    return [t.strip() for t in out.stdout.splitlines() if t.strip()]


def read_mdb_table(mdb_path: Path, table: str) -> pd.DataFrame:
    out = subprocess.run(
        ["mdb-export", "-D", "%Y-%m-%d %H:%M:%S", str(mdb_path), table],
        capture_output=True, text=True, check=True,
    )
    return pd.read_csv(io.StringIO(out.stdout), low_memory=False)


def save_upload_to_tempfile(uploaded_file, suffix: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getbuffer())
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


@st.cache_data(show_spinner=False)
def load_phdwin_mdb(file_bytes: bytes, filename: str) -> Dict[str, pd.DataFrame]:
    """Extract LseInfo / LseEco / MonInfo (and any other tables present) from a PHDWin .mdb."""
    suffix = Path(filename).suffix.lower() or ".mdb"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file_bytes); tmp.flush(); tmp.close()
    p = Path(tmp.name)
    if not mdbtools_available():
        raise RuntimeError(
            "mdbtools is not installed. Add `mdbtools` to packages.txt or pre-export "
            "your PHDWin tables to xlsx/csv and upload those instead."
        )
    tables = list_mdb_tables(p)
    out: Dict[str, pd.DataFrame] = {}
    for t in tables:
        try:
            out[t] = read_mdb_table(p, t)
        except Exception as e:
            st.warning(f"Skipped table `{t}`: {e}")
    return out


@st.cache_data(show_spinner=False)
def load_phdwin_xlsx(file_bytes: bytes) -> Dict[str, pd.DataFrame]:
    """PHDWin export workbook with sheets matching the expected table names."""
    xl = pd.ExcelFile(io.BytesIO(file_bytes))
    return {s: pd.read_excel(xl, sheet_name=s) for s in xl.sheet_names}


@st.cache_data(show_spinner=False)
def load_well_headers(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes), low_memory=False)
    return pd.read_excel(io.BytesIO(file_bytes))


@st.cache_data(show_spinner=False)
def load_los_workbook(file_bytes: bytes) -> Dict[str, pd.DataFrame]:
    """LOS tie-out workbook. Expects a `PowerBI_Long` sheet with columns
    Date, Category, Line Item, Value.
    """
    xl = pd.ExcelFile(io.BytesIO(file_bytes))
    out = {s: pd.read_excel(xl, sheet_name=s) for s in xl.sheet_names}
    if "PowerBI_Long" in out:
        df = out["PowerBI_Long"]
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        out["PowerBI_Long"] = df
    return out


def coerce_dates(df: pd.DataFrame, candidate_cols: List[str]) -> pd.DataFrame:
    for c in candidate_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def get_store() -> Dict[str, pd.DataFrame]:
    """Container for all loaded frames living in st.session_state['store']."""
    if "store" not in st.session_state:
        st.session_state["store"] = {}
    return st.session_state["store"]


def required_tables_present(required: List[str]) -> Optional[str]:
    store = get_store()
    missing = [t for t in required if t not in store or store[t] is None or store[t].empty]
    if missing:
        return "Missing required tables: " + ", ".join(f"`{m}`" for m in missing)
    return None
