# PHDWin / Aries QC — Streamlit replica of `QC_Tool_PHDWin_v01.pbix`

A Streamlit replica of the existing PowerBI QC report, with hooks for an Aries
database and uploadable Excel/CSV inputs. Designed to deploy on Streamlit
Community Cloud (Linux).

## Pages

24 PowerBI sections are mirrored 1-for-1:

1. Reserves Summary &nbsp;&nbsp; 2. Map &nbsp;&nbsp; 3. Oneline &nbsp;&nbsp; 4. Pie Chart
5. Gross Production &nbsp;&nbsp; 6. Net Production &nbsp;&nbsp; 7. Well Count
8. Net Revenue &nbsp;&nbsp; 9. Cash Flow &nbsp;&nbsp; 10. Net CF by Case
11. Opex ($/Boe) vs Time &nbsp;&nbsp; 12. Yield vs Shrink Plot &nbsp;&nbsp; 13. Yield/Shrink Box
14. Taxes Box &nbsp;&nbsp; 15. PV10 by Operator &nbsp;&nbsp; 16. PV10 by County
17. PV10 by LEASE_NAME &nbsp;&nbsp; 18. Reserves, Opex, Capex Check &nbsp;&nbsp; 19. ResCat & API Check
20. F&D, Opex % of Revenue &nbsp;&nbsp; 21. Sev Tax by Phase &nbsp;&nbsp; 22. Realized Prices
23. Volumes LOS Tie Out &nbsp;&nbsp; 24. Economics LOS Tie Out &nbsp;&nbsp; 25. Aries QC (stub)

The global page-level slicer **Reserve Category (RsvCat)** in the sidebar
matches the PowerBI page filter.

### Aries scenarios

Aries data carries a `SCENARIO` column. The sidebar **Aries scenario(s)**
multiselect picks one case (default = the case with monthly economics so
reserves and cashflow tie) or two+ to compare. With two+ selected, a
**Multi-scenario view** toggle appears:

- **Overlay** — scenarios become series on one chart (line, scatter, box).
- **Split** — a panel per scenario for every chart type.

A second scenario's monthly stream can come from the database (re-export with
that case's monthly run) or from a **monthly xls** appended in the sidebar.
Two xls layouts are auto-detected:

- **Raw `AC_MONTHLY`** — sheet `AC_MONTHLY` with Aries S-codes plus PROPNUM and
  OUTDATE. Per-well, same shape as the database table.
- **Monthly Summary** — sheet `Monthly Summary` with friendly columns
  (`Net Oil (Mbbl)`, `Total Revenue ($)`, ...) and `SE_RSV_CAT` + `Date`.
  Volumes in Mbbl/MMcf are scaled to Bbl/Mcf and derived columns (Net
  Equivalent (Boe), Opex ($/Boe), neg cols, Year, ...) are computed
  automatically so the rows line up with the database.
  Pre-aggregated, so per-lease charts show one combined series for this case.

### Chart options

Every chart has its own **Options** popover (button above the plot):

- **Y-axis scale** — Linear / Log, per plot.
- **Date range** — clip that plot's time axis (datetime or Year).
- **By-lease plots** (line & scatter coloured by lease) also get a **lease
  multiselect** and a **Roll up (combine all)** toggle to switch between
  per-lease breakout and a single aggregated series.

The sidebar **Chart options** section sets the *defaults* each plot's popover
starts from (handy for setting log scale or a date window globally, then
overriding individual plots).

## Inputs

Upload from the sidebar — all stored in `st.session_state`:

| Source | What to upload | Notes |
|---|---|---|
| PHDWin | `.mdb` / `.accdb` (preferred) **or** `.xlsx` | Parsed via `mdbtools`. `.accdb` requires mdbtools ≥ 1.0.0 (installed on Streamlit Cloud); if read fails, pre-export to xlsx. xlsx export must have sheets named `LseInfo`, `LseEco`, `MonInfo`. |
| Aries  | `.mdb` / `.accdb` / `.zip` / `.xlsx` | Reads `AC_PROPERTY`, `AC_ONELINE`, `AC_MONTHLY`, `AC_PRODUCT`. Reserve-category and lease columns are auto-detected (`SIPC_RSV_CAT` / `SE_RSV_CAT` / `RESCAT`; `LEASE_NAME` / `LEASE`), so different client setups load without edits. xlsx must have sheets named after the AC_ tables. |
| Well headers | `.csv` / `.xlsx` | Must contain surface latitude / longitude columns. |
| LOS tie-out | `.xlsx` | A `LOS_Data` sheet (`Date, Data, Category, Line Item, LOS Value, LTM, L6M, L3M`) — only `LOS Historical` rows are used — **or** a legacy `PowerBI_Long` sheet (`Date, Category, Line Item, Value`). Both are normalized automatically. |

## How it matches PowerBI (calculated columns)

The report's charts reference "friendly" columns — `Net Oil (Bbl)`, `PV10 ($)`,
`Total Opex ($)`, `Net Historical Oil (Bbl/d)`, etc. **These do not exist in the
raw PHDWin database.** They are DAX calculated columns PowerBI derives from the
raw fields. `app/lib/transform.py` reproduces every one of those formulas in
pandas, so uploading a raw `.accdb`/`.mdb` (or a raw export) renders the same
numbers as PowerBI. A few examples:

| Friendly column | Formula (from the .pbix) |
|---|---|
| `Net Oil (Bbl)` | `NetOil * 1000` |
| `PV10 ($)` | `PwC * 1000` |
| `Total Opex ($)` | `(Net_Lsecost + Net_Wellcost + Net_OtherCost + Net_OpCost) * 1000` |
| `BFIT CF ($)` | `Ndcash * 1000` |
| `Opex ($/Boe)` | `Total Opex ($) / Net Equivalent (Boe)` |
| `Net Historical Oil (Bbl/d)` | `(ProdHist/30.4) * ΣNetOil/ΣGrossOil` (MonInfo is long-format) |

The transforms were validated against the values PowerBI itself stored in the
`.pbix` DataModel — max difference 0. Enrichment runs automatically after upload
(`transform.enrich_store`); it only adds friendly columns that aren't already
present, so a PHDWin report export that already contains them is left untouched.

Raw tables the transform reads: `LseInfo`, `LseEco`, `MonInfo`, and optionally
`UnitLbl` (NGL unit handling) and `Asofdat` (differentials).

## Sample data

`data/samples/PHDWin_sample.xlsx` is a 6-lease subset of real PHDWin output in
**raw** form (sheets `LseInfo`, `LseEco`, `MonInfo`, `UnitLbl`, `Asofdat`).
Upload it via the PHDWin uploader to see every page populated without a database.

## Expected schema (PHDWin)

Column names come from the PowerBI report and must match. Key columns:

- **`LseInfo`**: `Lse_Id`, `LSE_NAME`, `RsvCat`, `OPER`, `County`, `WrkInt`, `RevInt`, `API*`
- **`LseEco`**: `Lse_Id`, `EcoDate`, `Net Oil (Bbl)`, `Net Gas (Mcf)`, `Net NGL (Bbl)`,
  `Net Equivalent (Boe)`, `Gross Oil (Bbl/d)`, `Gross Gas (Mcf/d)`,
  `Net Oil Revenue ($)`, `Net Gas Revenue ($)`, `Net NGL Revenue ($)`,
  `Total Revenue ($)`, `Total Opex ($)`, `Total Sev Tax ($)`, `Total Ad Val Tax ($)`,
  `Total Investment ($)`, `BFIT CF ($)`, `PV8 ($)`...`PV15 ($)`, `Opex ($/Boe)`,
  `NGL Yield (Bbl/MMcf)`, `Shrinkage`, `Sev. Tax/Boe`, `Ad Val Tax/Boe`,
  `Sev. Tax $/Bbl`, `Sev Tax $/Mcf`, `Sev. Tax NGL $/Bbl`,
  `Realized Oil Price ($/Bbl)`, `Realized Gas Price ($/Mcf)`,
  `F&D ($/Boe)`, `Opex % of Revenue`, `Net Capex ($)`
- **`MonInfo`**: `Lse_Id`, `Prod Date`, historical production columns
  (`Historical Oil Gross from Product (Bbl/d)`, etc.)

If your PHDWin export uses different names, rename them in the xlsx before
upload — or open an issue and the loader can be extended to alias them.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (done — branch `claude/adoring-brown-iN0Xn`).
2. Create a new app at https://share.streamlit.io pointing at `app/app.py`.
3. `packages.txt` installs `mdbtools` so Access uploads work on Linux. The
   Streamlit Cloud image ships with mdbtools ≥ 1.0.0, which has experimental
   `.accdb` support. Some Access 2007+ column types (Complex, attachments,
   multi-value) may not decode — if your `.accdb` fails to read, open it in
   Access and export the needed tables to xlsx, then upload that.

## Repo layout

```
app/
  app.py                # entry point, sidebar uploads, navigation
  lib/
    data_loader.py      # .mdb / xlsx / csv ingest
    filters.py          # RsvCat slicer
    model.py            # joins + derived columns (Prod Date, Year)
    charts.py           # Plotly helpers (pie, bar, line, treemap, box, scatter, map, table)
  pages/
    01_Reserves_Summary.py ... 25_Aries_QC.py
data/samples/           # sample CSV + xlsx
.streamlit/config.toml
requirements.txt
packages.txt            # apt packages for Streamlit Cloud (mdbtools)
```
