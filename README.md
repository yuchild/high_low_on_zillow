# high_low_on_zillow

Bay Area county-first Zillow research dashboard built with Streamlit.

## Data Layers
data/raw/zillow/              # downloaded Zillow CSVs
data/processed/               # cleaned parquet files
data/external/                # boundary files and external reference data

## Phase 1
- repo scaffold
- config-driven project setup
- Streamlit app entrypoint
- notebook + src package layout
- ready for Zillow ingestion in Phase 2

## Local setup
From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt

touch data/raw/.gitkeep data/interim/.gitkeep data/processed/.gitkeep data/external/.gitkeep

PYTHONPATH=src python scripts/bootstrap_dirs.py
PYTHONPATH=src pytest
PYTHONPATH=src streamlit run app.py

## Local pipeline

Run from repo root:

```bash
source .venv/bin/activate

PYTHONPATH=src python scripts/download_zillow_data.py
PYTHONPATH=src python scripts/build_bay_area_dataset.py
PYTHONPATH=src python scripts/build_kpi_tables.py
PYTHONPATH=src python scripts/download_county_geojson.py

PYTHONPATH=src pytest
PYTHONPATH=src streamlit run app.py

PYTHONPATH=src python scripts/build_kpi_tables.py
PYTHONPATH=src python scripts/validate_data.py