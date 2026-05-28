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
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st


PHDWIN_TABLES = ["LseInfo", "LseEco", "MonInfo"]
# Only these are needed to drive the report — reading just these keeps memory
# low on Streamlit Community Cloud (~1 GB RAM) instead of dumping every table.
PHDWIN_NEEDED = ["LseInfo", "LseEco", "MonInfo", "UnitLbl", "Asofdat"]
ARIES_TABLES = ["AC_PROPERTY", "AC_ECONOMIC", "AC_ONELINE", "AC_PRODUCT", "AC_DAILY"]


def mdbtools_available() -> bool:
    return shutil.which("mdb-tables") is not None and shutil.which("mdb-export") is not None


def mdbtools_version() -> Optional[str]:
    if not mdbtools_available():
        return None
    try:
        out = subprocess.run(["mdb-ver", "--help"], capture_output=True, text=True)
        # Fall back to `mdb-tables --version` which prints version + exits
        ver = subprocess.run(["mdb-tables", "--version"], capture_output=True, text=True)
        text = (ver.stdout or ver.stderr).strip().splitlines()
        return text[0] if text else None
    except Exception:
        return None


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
def load_access_db(file_bytes: bytes, filename: str,
                   only_tables: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """Extract tables from an Access `.mdb` or `.accdb` file.

    On Linux this uses `mdbtools`. `.mdb` (Jet 3/4) is fully supported; `.accdb`
    (Access 2007+) is supported by mdbtools >= 1.0.0 but with caveats — some
    column types (Complex, attachments, multivalue) may not decode. If the read
    fails, callers should fall back to uploading a pre-exported xlsx.

    If `only_tables` is given, only those tables are read (case-insensitive
    match), which keeps memory low. If none of them are present, all tables are
    read so unknown schemas still work.
    """
    suffix = Path(filename).suffix.lower() or ".mdb"
    if suffix not in (".mdb", ".accdb"):
        raise ValueError(f"Unsupported Access file extension: {suffix}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file_bytes); tmp.flush(); tmp.close()
    p = Path(tmp.name)
    if not mdbtools_available():
        raise RuntimeError(
            "`mdbtools` is not installed on this host. On Streamlit Community Cloud "
            "it's installed via packages.txt. Locally, install with "
            "`apt-get install mdbtools` (Linux) / `brew install mdbtools` (Mac), "
            "or pre-export your tables to xlsx/csv."
        )
    try:
        tables = list_mdb_tables(p)
    except subprocess.CalledProcessError as e:
        hint = ""
        if suffix == ".accdb":
            hint = (
                " — your mdbtools build may not support .accdb (need >= 1.0.0). "
                "Pre-export your tables to xlsx and upload that instead."
            )
        raise RuntimeError(f"Could not read tables from {filename}{hint}\n{e.stderr}") from e

    if only_tables:
        wanted = {t.lower() for t in only_tables}
        selected = [t for t in tables if t.lower() in wanted]
        if selected:  # only narrow if we actually matched something
            tables = selected

    out: Dict[str, pd.DataFrame] = {}
    for t in tables:
        try:
            out[t] = _downcast(read_mdb_table(p, t))
        except Exception as e:
            st.warning(f"Skipped table `{t}`: {e}")
    return out


@st.cache_data(show_spinner=False)
def load_access_zip(file_bytes: bytes, filename: str,
                    only_tables: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """Read an Access `.mdb`/`.accdb` that's been zipped.

    Raw Access files are frequently blocked at the network layer (firewall,
    antivirus, browser, cloud proxy) and fail to upload with an "Axios Network
    error". Zipping sidesteps that. We extract the first .mdb/.accdb member and
    parse it with the normal Access loader.
    """
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        members = [n for n in zf.namelist()
                   if n.lower().endswith((".mdb", ".accdb")) and not n.startswith("__MACOSX")]
        if not members:
            raise RuntimeError(
                "No .mdb or .accdb file found inside the zip. "
                "Zip the Access database (not a folder of other files)."
            )
        member = members[0]
        inner_bytes = zf.read(member)
    return load_access_db(inner_bytes, Path(member).name, only_tables=only_tables)


def _downcast(df: pd.DataFrame) -> pd.DataFrame:
    """Shrink float64/int64 columns to reduce memory footprint."""
    for c in df.select_dtypes(include=["float64"]).columns:
        df[c] = pd.to_numeric(df[c], downcast="float")
    for c in df.select_dtypes(include=["int64"]).columns:
        df[c] = pd.to_numeric(df[c], downcast="integer")
    return df


# Backwards-compatible alias
load_phdwin_mdb = load_access_db


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
