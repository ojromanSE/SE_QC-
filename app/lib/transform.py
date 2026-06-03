"""Replicate the PowerBI calculated columns from raw PHDWin tables.

The QC_Tool_PHDWin_v01.pbix report charts reference "friendly" columns
(e.g. "Net Oil (Bbl)", "PV10 ($)", "Net Historical Oil (Bbl/d)") that do NOT
exist in the raw PHDWin .accdb/.mdb. They are DAX calculated columns built on
the raw fields. This module reproduces those formulas in pandas so a raw
PHDWin upload renders identically to PowerBI.

Formulas were extracted directly from the .pbix DataModel. Constants:
- *1000      : PHDWin stores volumes/$ in thousands
- /30.4      : monthly -> per-day
- /6         : Mcf gas -> Boe
- /42        : NGL gallons -> barrels (only when UnitLbl base unit is "gal")

Aggregate-context columns (Shrinkage, Net Historical *) use whole-table
SUM/AVG, matching DAX calculated-column semantics (no relationship filter).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

DAYS_PER_MONTH = 30.4
GAS_BOE_DIVISOR = 6.0
THOUSAND = 1000.0


def _safe_div(num, den, fallback=0.0):
    num = pd.to_numeric(num, errors="coerce")
    den = pd.to_numeric(den, errors="coerce")
    out = num / den
    return out.replace([np.inf, -np.inf], np.nan).fillna(fallback)


def _ngl_in_gallons(unit_lbl: pd.DataFrame | None) -> bool:
    """LOOKUPVALUE(UnitLbl[BaseUnits], UnitLbl[Product]="NGL") == "gal"."""
    if unit_lbl is None or "Product" not in unit_lbl.columns or "BaseUnits" not in unit_lbl.columns:
        return False
    rows = unit_lbl[unit_lbl["Product"].astype(str).str.upper() == "NGL"]
    if rows.empty:
        return False
    return str(rows["BaseUnits"].iloc[0]).strip().lower() == "gal"


def enrich_lse_eco(eco: pd.DataFrame, lse_info: pd.DataFrame | None = None,
                   unit_lbl: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add all LseEco DAX calculated columns. Idempotent and column-safe:
    if a friendly column already exists (e.g. PHDWin report export), it is kept.
    """
    df = eco.copy()
    have = set(df.columns)
    ngl_gal = _ngl_in_gallons(unit_lbl)

    def col(name):  # raw column accessor as float Series (0 if absent)
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce")
        return pd.Series(np.nan, index=df.index)

    def setf(name, series):
        if name not in have:  # don't clobber an export's own value
            df[name] = series

    # Revenue
    setf("Net Oil Revenue ($)", col("CoNetRevOil") * THOUSAND)
    setf("Net Gas Revenue ($)", col("CoNetRevGas") * THOUSAND)
    setf("Net NGL Revenue ($)", col("CoNetRevNgl") * THOUSAND)
    setf("Total Revenue ($)", df.get("Net Gas Revenue ($)", 0) + df.get("Net Oil Revenue ($)", 0) + df.get("Net NGL Revenue ($)", 0))

    # Gross / Net volumes
    setf("Gross Oil (BBl)", col("GrossOil") * THOUSAND)
    setf("Gross Oil (Bbl/d)", col("GrossOil") * THOUSAND / DAYS_PER_MONTH)
    setf("Gross Gas (Mcf)", col("GrossGas") * THOUSAND)
    setf("Gross Gas (Mcf/d)", col("GrossGas") * THOUSAND / DAYS_PER_MONTH)
    setf("Net Oil (Bbl)", col("NetOil") * THOUSAND)
    setf("Net Oil (Bbl/d)", col("NetOil") * THOUSAND / DAYS_PER_MONTH)
    setf("Net Gas (Mcf)", col("NetGas") * THOUSAND)
    setf("Net Gas (Mcf/d)", col("NetGas") * THOUSAND / DAYS_PER_MONTH)

    ngl = col("NetNgl")
    gross_ngl = col("GrossNgl")
    if ngl_gal:
        setf("Net NGL (Bbl)", ngl / 42 * THOUSAND)
        setf("Net NGL (Bbl/d)", ngl / 42 * THOUSAND / DAYS_PER_MONTH)
        setf("Gross NGL (Bbl)", gross_ngl / 42 * THOUSAND)
        setf("Gross NGL (Bbl/d)", gross_ngl / 42 * THOUSAND / DAYS_PER_MONTH)
    else:
        setf("Net NGL (Bbl)", ngl * THOUSAND)
        setf("Net NGL (Bbl/d)", ngl * THOUSAND / DAYS_PER_MONTH)
        setf("Gross NGL (Bbl)", gross_ngl * THOUSAND)
        setf("Gross NGL (Bbl/d)", gross_ngl * THOUSAND / DAYS_PER_MONTH)

    setf("Gross Equivalent (Boe/d)", df["Gross Oil (Bbl/d)"] + df["Gross Gas (Mcf/d)"] / GAS_BOE_DIVISOR)
    setf("Net Equivalent (Boe/d)", df["Net Oil (Bbl/d)"] + df["Net NGL (Bbl/d)"] + df["Net Gas (Mcf/d)"] / GAS_BOE_DIVISOR)
    setf("Net Equivalent (Boe)", df["Net Oil (Bbl)"] + df["Net NGL (Bbl)"] + df["Net Gas (Mcf)"] / GAS_BOE_DIVISOR)
    setf("Gross boe", df["Gross Oil (BBl)"] + df["Gross Gas (Mcf)"] / GAS_BOE_DIVISOR + df["Gross NGL (Bbl)"])

    # Costs / cash flow
    opex_raw = (col("Net_Lsecost") + col("Net_Wellcost") + col("Net_OtherCost") + col("Net_OpCost"))
    setf("Total Opex ($)", opex_raw * THOUSAND)
    setf("Total Opex ($) neg", opex_raw * -1 * THOUSAND)
    setf("Total Sev Tax ($) neg", col("Net_ProdTax") * -1 * THOUSAND)
    setf("Total Ad Val Tax neg ($)", col("Net_Adv") * -1 * THOUSAND)
    setf("Total Investment ($) neg", col("Net_Inv") * -1 * THOUSAND)
    setf("Net Capex ($)", df["Total Investment ($) neg"] * -1)
    setf("BFIT CF ($)", col("Ndcash") * THOUSAND)

    # Severance taxes
    setf("Sev Tax Gas ($)", col("ProdTaxGas") * THOUSAND)
    setf("Sev Tax Oil ($)", col("ProdTaxOil") * THOUSAND)
    setf("Sev Tax NGL ($)", col("ProdTaxNgl"))  # note: no *1000 in the report
    setf("Sev. Tax Oil $/Bbl", _safe_div(df["Sev Tax Oil ($)"], df["Net Oil (Bbl)"]))
    setf("Sev Tax $/Mcf", _safe_div(df["Sev Tax Gas ($)"], df["Net Gas (Mcf)"]))
    setf("Sev. Tax NGL $/Bbl", _safe_div(df["Sev Tax NGL ($)"], df["Net NGL (Bbl)"]))
    setf("Ad Val Tax/Boe", _safe_div(df["Total Ad Val Tax neg ($)"] * -1, df["Net Equivalent (Boe)"]))
    # Aliases used by report pages
    setf("Sev. Tax $/Bbl", df["Sev. Tax Oil $/Bbl"])
    setf("Sev. Tax/Boe", _safe_div(col("Net_ProdTax") * THOUSAND, df["Net Equivalent (Boe)"]))
    setf("Total Sev Tax ($)", col("Net_ProdTax") * THOUSAND)
    setf("Total Ad Val Tax ($)", col("Net_Adv") * THOUSAND)
    setf("Total Investment ($)", col("Net_Inv") * THOUSAND)

    # Ratios / prices
    setf("Opex ($/Boe)", _safe_div(df["Total Opex ($)"], df["Net Equivalent (Boe)"]))
    setf("Opex % of Revenue", _safe_div(df["Total Opex ($)"], df["Total Revenue ($)"]) * 100)
    setf("Realized Oil Price ($/Bbl)", _safe_div(df["Net Oil Revenue ($)"], df["Net Oil (Bbl)"]))
    setf("Realized Gas Price ($/Mcf)", _safe_div(df["Net Gas Revenue ($)"], df["Net Gas (Mcf)"]))
    setf("F&D ($/Boe)", _safe_div(df["Net Capex ($)"], df["Net Equivalent (Boe)"]))

    # PV columns
    setf("PV8 ($)", col("PwA") * THOUSAND)
    setf("PV9 ($)", col("PwB") * THOUSAND)
    setf("PV10 ($)", col("PwC") * THOUSAND)
    setf("PV12 ($)", col("PwD") * THOUSAND)
    setf("PV15 ($)", col("PwE") * THOUSAND)

    # Yields / shrink (NRI total mirrors DAX SUM(LseInfo[NRI]) with no row filter)
    nri_total = None
    if lse_info is not None and "NRI" in lse_info.columns:
        nri_total = pd.to_numeric(lse_info["NRI"], errors="coerce").sum()
    if nri_total and nri_total != 0:
        setf("Shrinkage", _safe_div(df["Net Gas (Mcf)"] / nri_total, df["Gross Gas (Mcf)"], fallback=1.0))
    else:
        setf("Shrinkage", pd.Series(1.0, index=df.index))
    setf("NGL Yield (Bbl/MMcf)", _safe_div(df["Gross NGL (Bbl)"], df["Gross Gas (Mcf)"]) * 100)
    setf("NGL Yield1 (Bbl/MMcf)", _safe_div(df["Gross NGL (Bbl)"], df["Gross Gas (Mcf)"]))

    # Date / Year helpers
    dcol = "EcoDate" if "EcoDate" in df.columns else None
    if dcol:
        df["EcoDate"] = pd.to_datetime(df[dcol], errors="coerce")
        df["Prod Date"] = df["EcoDate"]
        df["Year"] = df["EcoDate"].dt.year
    return df


def enrich_mon_info(mon: pd.DataFrame, eco_enriched: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add MonInfo DAX calculated columns. MonInfo is long-format: one row per
    product (ProdName) per date (ProdDate); ProdHist is the monthly historical
    volume. The Net Historical * columns use whole-table SUM/AVG ratios off
    LseEco, matching the DAX calculated-column behaviour.
    """
    df = mon.copy()
    have = set(df.columns)
    name = df["ProdName"].astype(str) if "ProdName" in df.columns else pd.Series("", index=df.index)
    hist = pd.to_numeric(df["ProdHist"], errors="coerce") if "ProdHist" in df.columns else pd.Series(np.nan, index=df.index)

    def setf(c, s):
        if c not in have:
            df[c] = s

    oil_d = np.where(name.eq("Oil"), hist / DAYS_PER_MONTH, 0.0)
    gas_d = np.where(name.eq("Gas"), hist / DAYS_PER_MONTH, 0.0)
    wtr_d = np.where(name.eq("Water"), hist / DAYS_PER_MONTH, 0.0)
    ngl_d = np.where(name.eq("NGL"), hist / DAYS_PER_MONTH / 42, 0.0)
    setf("Historical Oil Gross from Product (Bbl/d)", oil_d)
    setf("Historical Gas Gross from Product (Mscf/d)", gas_d)
    setf("Historical Water Gross from Product (Bbl/d)", wtr_d)
    setf("Historical NGL Gross from Product (Bbl/d)", ngl_d)
    setf("Historical Equivalent Gross from Product (Boe/d)",
         df["Historical Oil Gross from Product (Bbl/d)"] + df["Historical Gas Gross from Product (Mscf/d)"] / GAS_BOE_DIVISOR)

    # Global net/gross ratios off LseEco (DAX SUM/AVG over the whole table)
    oil_ratio = gas_ratio = ngl_over_gas = np.nan
    if eco_enriched is not None:
        sgo = pd.to_numeric(eco_enriched.get("Gross Oil (BBl)"), errors="coerce").sum()
        sno = pd.to_numeric(eco_enriched.get("Net Oil (Bbl)"), errors="coerce").sum()
        sgg = pd.to_numeric(eco_enriched.get("Gross Gas (Mcf)"), errors="coerce").sum()
        sng = pd.to_numeric(eco_enriched.get("Net Gas (Mcf)"), errors="coerce").sum()
        ann = pd.to_numeric(eco_enriched.get("Net NGL (Bbl)"), errors="coerce").mean()
        ang = pd.to_numeric(eco_enriched.get("Net Gas (Mcf)"), errors="coerce").mean()
        oil_ratio = (sno / sgo) if sgo else np.nan
        gas_ratio = (sng / sgg) if sgg else np.nan
        ngl_over_gas = (ann / ang) if ang else np.nan

    setf("Net Historical Oil (Bbl/d)", df["Historical Oil Gross from Product (Bbl/d)"] * (oil_ratio if pd.notna(oil_ratio) else 0))
    setf("Net Historical Gas (Mcf/d)", df["Historical Gas Gross from Product (Mscf/d)"] * (gas_ratio if pd.notna(gas_ratio) else 0))
    setf("Net Historical NGL (Bbl/d)", (ngl_over_gas if pd.notna(ngl_over_gas) else 0) * df["Net Historical Gas (Mcf/d)"])
    setf("Net Historical Equivalent (Boe/d)",
         df["Net Historical Oil (Bbl/d)"] + df["Net Historical NGL (Bbl/d)"] + df["Net Historical Gas (Mcf/d)"] / GAS_BOE_DIVISOR)
    # Alias for report page that says "Net Historical Gas Sold (Mcf/d)"
    setf("Net Historical Gas Sold (Mcf/d)", df["Net Historical Gas (Mcf/d)"])

    dcol = "ProdDate" if "ProdDate" in df.columns else None
    if dcol:
        df["ProdDate"] = pd.to_datetime(df[dcol], errors="coerce")
        df["Prod Date"] = df["ProdDate"]
        df["Year"] = df["ProdDate"].dt.year
    return df


def enrich_asofdat(asof: pd.DataFrame) -> pd.DataFrame:
    df = asof.copy()
    if "NGL Diff" not in df.columns and "DiffPercent" in df.columns:
        df["NGL Diff"] = 1 - ((pd.to_numeric(df["DiffPercent"], errors="coerce") * -1) / 100)
    return df


def enrich_store(store: dict) -> dict:
    """Run all PHDWin enrichments in dependency order on the session store.

    Safe to call repeatedly: each enricher only adds friendly columns that
    aren't already present, so re-running after a new upload is a no-op for
    already-derived columns.
    """
    info = store.get("LseInfo")
    unit = store.get("UnitLbl")
    eco = store.get("LseEco")
    if eco is not None and "PV10 ($)" not in eco.columns:
        store["LseEco"] = enrich_lse_eco(eco, info, unit)
    mon = store.get("MonInfo")
    if mon is not None and "Net Historical Oil (Bbl/d)" not in mon.columns:
        store["MonInfo"] = enrich_mon_info(mon, store.get("LseEco"))
    asof = store.get("Asofdat")
    if asof is not None and "NGL Diff" not in asof.columns:
        store["Asofdat"] = enrich_asofdat(asof)
    return store
