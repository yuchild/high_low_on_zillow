# high_low_on_zillow

A Streamlit dashboard for analyzing Bay Area housing trends using Zillow Research data.

This project supports **mixed geographic levels**:
- County-level: home prices, rents
- Metro-level: inventory, sales activity

---

## Features

- 📊 KPI dashboards (MoM, YoY, rankings)
- 🗺 County-level geospatial heatmaps
- 📈 Time-series trends (county + metro)
- 🧱 Config-driven ingestion pipeline
- 🧪 Tests + validation scripts

---

## Project Structure

---

## Quick Start (Local)

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt
```

Initialize directories:

```bash
touch data/raw/.gitkeep data/interim/.gitkeep data/processed/.gitkeep data/external/.gitkeep
```

Run tests:

```bash
PYTHONPATH=src pytest
```

Run app:

```bash
PYTHONPATH=src streamlit run app.py
```

## Data Pipeline

Run the full pipeline:

```bash
PYTHONPATH=src python scripts/download_zillow_data.py
PYTHONPATH=src python scripts/build_bay_area_dataset.py
PYTHONPATH=src python scripts/build_kpi_tables.py
PYTHONPATH=src python scripts/download_county_geojson.py
```

Validate output:

```bash
PYTHONPATH=src python scripts/validate_data.py
```

## Data Sources

All datasets come from:
👉 https://www.zillow.com/research/data/

Current usage:
| Dataset            | Geography | Purpose         |
| ------------------ | --------- | --------------- |
| Home Prices (ZHVI) | County    | Price trends    |
| Rent (ZORI)        | County    | Rental trends   |
| Inventory          | Metro     | Market supply   |
| Sales              | Metro     | Market activity |

## Deployment (Streamlit Cloud)

Requirements:
app.py at repot root
requirements.txt (no GDAL dependencies)

Key notes:
Uses sys.path injection for src/ imports
Requires data/processed/ and data/external/ to be committed

## Testing

Run:

```bash
PYTHONPATH=src pytest
```

Includes:
schema validation
processed data checks
KPI consistency

## Future Improvements
Add affordability metrics
Expand to ZIP / city-level data
Composite “market hotness” score
UI enhancements (filters, colors, tooltips)