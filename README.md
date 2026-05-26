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

## Inputs

Upload from the sidebar — all stored in `st.session_state`:

| Source | What to upload | Notes |
|---|---|---|
| PHDWin | `.mdb` / `.accdb` (preferred) **or** `.xlsx` | Parsed via `mdbtools`. `.accdb` requires mdbtools ≥ 1.0.0 (installed on Streamlit Cloud); if read fails, pre-export to xlsx. xlsx export must have sheets named `LseInfo`, `LseEco`, `MonInfo`. |
| Aries  | `.mdb` / `.accdb` | Tables loaded into a separate namespace; Aries page is a stub until you share a chart spec. |
| Well headers | `.csv` / `.xlsx` | Must contain surface latitude / longitude columns. |
| LOS tie-out | `.xlsx` | Must include a `PowerBI_Long` sheet with `Date, Category, Line Item, Value`. |

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
