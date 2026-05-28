"""Replicate the Aries QC PowerBI model (QC_Tool__Aries_v010.pbix) from a raw
Aries .mdb.

The report renames Aries column codes (S/C/M/B) to friendly names in Power
Query, then adds DAX calculated columns. Raw Aries tables hold only the codes,
so a raw .mdb upload needs both steps. Mappings and formulas were extracted
directly from the .pbix (Power Query M + DAX) and validated against the values
PowerBI stored in the DataModel.

Tables used: AC_PROPERTY (lease headers), AC_ONELINE (per-lease reserves/PV),
AC_MONTHLY (monthly economics), AC_PRODUCT (historical production).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

DPM = 30.4   # days per month
BOE = 6.0    # Mcf gas per Boe

# --- Power Query column renames (code -> friendly) -------------------------
MONTHLY_RENAME = {
    "S370": "Gross Oil (Bbl)", "S195": "Oil Price ($/bbl)", "S196": "Gas Price ($/Mcf)",
    "S199": "NGL Price ($/bbl)", "S846": "Net Oil Revenue ($)", "S847": "Net Gas Revenue ($)",
    "S848": "Net CND Revenue ($)", "S850": "Net NGL Revenue ($)", "S872": "Oil Sev Tax ($)",
    "S873": "Gas Sev Tax ($)", "S874": "CND Sev Tax ($)", "S876": "NGL Sev Tax ($)",
    "S887": "Total Sev Tax ($)", "S1064": "Total Ad Val Tax ($)", "S1018": "Oil Variable Opex ($)",
    "S1019": "Gas Variable Opex ($)", "S1020": "CND Variable Opex ($)", "S1022": "NGL Variable Opex ($)",
    "S1024": "Water Variable Opex ($)", "S1033": "Fixed Opex ($)", "S1039": "Liquids Transportation Cost ($)",
    "S1040": "Gas Transportation Cost ($)", "S1062": "Total Opex ($)", "S371": "Gross Gas (Mcf)",
    "S372": "Gross CND (Bbl)", "S374": "Gross NGL (Bbl)", "S376": "Gross Water (Bbl)",
    "S800": "Net Oil (Bbl)", "S816": "Net Gas (Mcf)", "S802": "Net CND (Bbl)",
    "S804": "Net NGL (Bbl)", "S806": "Net Water (Bbl)",
}
ONELINE_RENAME = {
    "M4": "Life of Project (yrs)", "M6": "Calculation Date", "M101": "Input Settings",
    "M31": "Initial Approx WI", "M41": "Initial Approx NRI", "M21": "Gross EUR Oil (Bbl)",
    "M22": "Gross EUR Gas (Mcf)", "C370": "Gross Res Oil (Bbl)", "C371": "Gross Res Gas (Mcf)",
    "C374": "Gross Res NGL (Bbl)", "C815": "Net Res Oil (Bbl)", "C372": "Gross Res CND (Bbl)",
    "C816": "Net Res Gas (Mcf)", "C819": "Net Res NGL (Mcf)", "C821": "Net Water (Bbl)",
    "C846": "Net Oil Revenue ($)", "C847": "Net Gas Revenue ($)", "C848": "Net CND Revenue ($)",
    "C850": "Net NGL Revenue ($)", "C861": "Net Total Revenue ($)", "C887": "Net Sev Tax ($)",
    "C1064": "Net Ad Val Tax ($)", "C1062": "Net Operating Expense ($)", "M16": "Effective Date",
    "C817": "Net Res CND (Bbl)", "C1183": "Net Capex ($)", "C1101": "BFIT CF ($)",
    "E1": "BFIT IRR (%)", "E3": "BFIT Payout (yrs)", "E7": "BFIT ROI",
    "B1": "PV8 ($)", "B2": "PV10 ($)", "B3": "PV15 ($)", "B4": "PV20 ($)",
    "B5": "PV25 ($)", "B6": "PV28 ($)", "B7": "PV30 ($)", "B8": "PV35 ($)",
}


def _num(df, c):
    return pd.to_numeric(df[c], errors="coerce") if c in df.columns else pd.Series(np.nan, index=df.index)


def _safe_div(num, den, fallback=0.0):
    out = pd.to_numeric(num, errors="coerce") / pd.to_numeric(den, errors="coerce")
    return out.replace([np.inf, -np.inf], np.nan).fillna(fallback)


def enrich_oneline(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={k: v for k, v in ONELINE_RENAME.items() if k in df.columns}).copy()
    have = set(df.columns)

    def setf(c, s):
        if c not in have:
            df[c] = s

    setf("Net Equivalent (Boe)", _num(df, "Net Res Oil (Bbl)") + _num(df, "Net Res NGL (Mcf)") + _num(df, "Net Res Gas (Mcf)") / BOE)
    setf("% Oil", _safe_div(df.get("Net Res Oil (Bbl)"), df["Net Equivalent (Boe)"]))
    setf("NGL Yield (Bbl/MMcf)", _safe_div(_num(df, "Gross Res NGL (Bbl)"), _num(df, "Gross Res Gas (Mcf)")) * 1000)
    setf("Shrinkage", _safe_div(_num(df, "Net Res Gas (Mcf)") / _num(df, "Initial Approx NRI"), _num(df, "Gross Res Gas (Mcf)"), fallback=1.0))
    setf("Opex ($/Boe)", _safe_div(_num(df, "Net Operating Expense ($)"), df["Net Equivalent (Boe)"]))
    setf("F&D ($/BOE)", _safe_div(_num(df, "Net Capex ($)"), df["Net Equivalent (Boe)"]))
    return df


def enrich_monthly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={k: v for k, v in MONTHLY_RENAME.items() if k in df.columns}).copy()
    have = set(df.columns)

    def setf(c, s):
        if c not in have:
            df[c] = s

    # Revenue / investment / cash flow (S-codes that stay raw: S861, S864-869, S750/751/1069, S1041-1049)
    setf("Other Revenue ($)", sum(_num(df, c) for c in ["S864", "S865", "S866", "S867", "S868", "S869"]))
    setf("Total Revenue ($)", sum(_num(df, c) for c in ["S861", "S864", "S865", "S866", "S867", "S868", "S869"]))
    setf("Other Deductions ($)", _num(df, "Liquids Transportation Cost ($)") + _num(df, "Gas Transportation Cost ($)")
         + sum(_num(df, c) for c in ["S1041", "S1042", "S1043", "S1044", "S1045", "S1046", "S1047", "S1048", "S1049"]))
    setf("Total Investment ($)", _num(df, "S750") + _num(df, "S751"))
    setf("BFIT CF ($)", _num(df, "S1069") - _num(df, "S750") - _num(df, "S751"))

    # Volumes & equivalents
    setf("Net Equivalent (Boe)", _num(df, "Net Oil (Bbl)") + _num(df, "Net NGL (Bbl)") + _num(df, "Net Gas (Mcf)") / BOE)
    setf("Net Oil (Bbl/d)", _num(df, "Net Oil (Bbl)") / DPM)
    setf("Net Gas (Mcf/d)", _num(df, "Net Gas (Mcf)") / DPM)
    setf("Net NGL (Bbl/d)", _num(df, "Net NGL (Bbl)") / DPM)
    setf("Net Water (Bbl/d)", _num(df, "Net Water (Bbl)") / DPM)
    setf("Gross Oil (Bbl/d)", _num(df, "Gross Oil (Bbl)") / DPM)
    setf("Gross Gas (Mcf/d)", _num(df, "Gross Gas (Mcf)") / DPM)
    setf("Gross Water (Bbl/d)", _num(df, "Gross Water (Bbl)") / DPM)
    setf("Gross Equivalent (Boe/d)", _num(df, "Gross Oil (Bbl)") / DPM + _num(df, "Gross Gas (Mcf)") / (DPM * BOE))
    setf("Net Equivalent (Boe/d)", df["Net Oil (Bbl/d)"] + df["Net NGL (Bbl/d)"] + df["Net Gas (Mcf/d)"] / BOE)

    # Negatives for cash-flow stack
    setf("Total Sev Tax ($) neg", _num(df, "Total Sev Tax ($)") * -1)
    setf("Total Ad Val Tax ($) neg", _num(df, "Total Ad Val Tax ($)") * -1)
    setf("Total Opex ($) neg", _num(df, "Total Opex ($)") * -1)
    setf("Total Investment ($) neg", df["Total Investment ($)"] * -1)

    # Ratios
    setf("Opex ($/Boe)", _safe_div(_num(df, "Total Opex ($)"), df["Net Equivalent (Boe)"]))
    setf("Sev. Tax/BOE", _safe_div(_num(df, "Total Sev Tax ($)"), df["Net Equivalent (Boe)"]))
    setf("Ad Val Tax/BOE", _safe_div(_num(df, "Total Ad Val Tax ($)"), df["Net Equivalent (Boe)"]))
    setf("Oil Rev/Bbl", _safe_div(_num(df, "Net Oil Revenue ($)"), _num(df, "Net Oil (Bbl)")))
    setf("Gas Rev/Mcf", _safe_div(_num(df, "Net Gas Revenue ($)"), _num(df, "Net Gas (Mcf)")))
    setf("NGL Rev/Bbl", _safe_div(_num(df, "Net NGL Revenue ($)"), _num(df, "Net NGL (Bbl)")))
    setf("Sev Tax/Bbl", _safe_div(_num(df, "Oil Sev Tax ($)"), _num(df, "Net Oil (Bbl)")))
    setf("Sev Tax/Mcf", _safe_div(_num(df, "Gas Sev Tax ($)"), _num(df, "Net Gas (Mcf)")))
    setf("Sev Tax/BNGL", _safe_div(_num(df, "NGL Sev Tax ($)"), _num(df, "Net NGL (Bbl)")))
    setf("Opex % of Revenue", _safe_div(_num(df, "Total Opex ($)"), df["Total Revenue ($)"]) * 100)
    setf("Forecasted", "Forecasted")

    if "OUTDATE" in df.columns:
        df["OUTDATE"] = pd.to_datetime(df["OUTDATE"], errors="coerce")
        df["Prod Date"] = df["OUTDATE"]
        df["OutYear"] = df["OUTDATE"].dt.year
        df["Year"] = df["OutYear"]
    return df


def enrich_product(df: pd.DataFrame, monthly: pd.DataFrame | None, oneline: pd.DataFrame | None) -> pd.DataFrame:
    df = df.copy()
    have = set(df.columns)

    def setf(c, s):
        if c not in have:
            df[c] = s

    setf("Historical Oil Gross from Product (Bbl/d)", _num(df, "OIL") / DPM)
    setf("Historical Gas Gross from Product (Bbl/d)", _num(df, "GAS") / DPM)
    setf("Historical Water Gross from Product (bbl/d)", _num(df, "WATER") / DPM)
    setf("Historical Equivalent Gross from Product (Bbl/d)", _num(df, "OIL") / DPM + _num(df, "GAS") / (DPM * BOE))

    # Global ratios off AC_MONTHLY / AC_ONELINE (DAX SUM/AVG over whole table)
    def agg(frame, col, how="sum"):
        if frame is None or col not in frame.columns:
            return np.nan
        s = pd.to_numeric(frame[col], errors="coerce")
        return s.sum() if how == "sum" else s.mean()

    oil_ratio = _ratio(agg(monthly, "Net Oil (Bbl)"), agg(monthly, "Gross Oil (Bbl)"))
    gas_ratio = _ratio(agg(monthly, "Net Gas (Mcf)"), agg(monthly, "Gross Gas (Mcf)"))
    ngl_over_gas = _ratio(agg(monthly, "Net NGL (Bbl)", "avg"), agg(monthly, "Net Gas (Mcf)", "avg"))
    gas_sold_ratio = _ratio(agg(oneline, "Net Res Gas (Mcf)"), agg(oneline, "Gross Res Gas (Mcf)"))
    nri_avg = agg(oneline, "Initial Approx NRI", "avg")

    setf("Net Historical Oil (bbl/d)", df["Historical Oil Gross from Product (Bbl/d)"] * _f(oil_ratio))
    setf("Net Historical Gas (Mcf/d)", df["Historical Gas Gross from Product (Bbl/d)"] * _f(gas_ratio))
    setf("Net Historical Water (Bbl/d)", df["Historical Water Gross from Product (bbl/d)"] * _f(nri_avg))
    setf("Net Historical NGL (Bbl/d)", _f(ngl_over_gas) * df["Net Historical Gas (Mcf/d)"])
    setf("Net Historical Gas Sold (Mcf/d)", df["Historical Gas Gross from Product (Bbl/d)"] * _f(gas_sold_ratio))
    setf("Net Historical Equivalent (Boe/d)",
         df["Net Historical Oil (bbl/d)"] + df["Net Historical NGL (Bbl/d)"] + df["Net Historical Gas Sold (Mcf/d)"] / BOE)

    if "P_DATE" in df.columns:
        df["P_DATE"] = pd.to_datetime(df["P_DATE"], errors="coerce")
        df["Prod Date"] = df["P_DATE"]
        df["Year"] = df["P_DATE"].dt.year
    return df


def _ratio(a, b):
    return (a / b) if (b not in (0, None) and pd.notna(b) and pd.notna(a)) else np.nan


def _f(x):
    return x if pd.notna(x) else 0.0


def enrich_aries_store(store: dict) -> dict:
    """Rename + enrich the Aries tables held under store['__aries__']."""
    a = store.get("__aries__")
    if not a:
        return store
    if "AC_ONELINE" in a and "Net Equivalent (Boe)" not in a["AC_ONELINE"].columns:
        a["AC_ONELINE"] = enrich_oneline(a["AC_ONELINE"])
    if "AC_MONTHLY" in a and "Net Equivalent (Boe)" not in a["AC_MONTHLY"].columns:
        a["AC_MONTHLY"] = enrich_monthly(a["AC_MONTHLY"])
    if "AC_PRODUCT" in a and "Net Historical Oil (bbl/d)" not in a["AC_PRODUCT"].columns:
        a["AC_PRODUCT"] = enrich_product(a["AC_PRODUCT"], a.get("AC_MONTHLY"), a.get("AC_ONELINE"))
    return store
