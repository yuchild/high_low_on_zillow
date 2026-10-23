#!/usr/bin/env python3
"""Build top-100 US metropolitan-area registries from official Census sources.

Outputs (only after validation):
  geography_registry/metros.csv
  geography_registry/metro_counties.csv

Uses 2025 Census population estimates for ranking and July 2023 OMB
delineations for county membership. Run from repository root.
"""
from __future__ import annotations
import argparse
import io
import re
from pathlib import Path
from urllib.request import Request, urlopen
import pandas as pd

POP_URL = ("https://www2.census.gov/programs-surveys/popest/datasets/"
           "2020-2025/metro/totals/cbsa-est2025-alldata.csv")
DELINEATION_URL = ("https://www2.census.gov/programs-surveys/metro-micro/geographies/"
                   "reference-files/2023/delineation-files/list1_2023.xlsx")

# Preserve existing keys so downstream dashboards do not lose their references.
EXISTING = {
    "35620":"new_york", "31080":"los_angeles", "16980":"chicago",
    "26420":"houston", "38060":"phoenix", "37980":"philadelphia",
    "41700":"san_antonio", "41740":"san_diego", "19100":"dallas_fort_worth",
    "27260":"jacksonville", "12420":"austin", "16740":"charlotte",
    "18140":"columbus", "26900":"indianapolis", "42660":"seattle",
    "19740":"denver", "36420":"oklahoma_city",
}

def fetch(url, local_path=None):
    if local_path:
        return Path(local_path).read_bytes()
    req = Request(url, headers={"User-Agent": "ZillowEDA/1.0 (Census public data)"})
    with urlopen(req, timeout=90) as response:
        return response.read()

def norm(x):
    return re.sub(r"[^a-z0-9]+", " ", str(x).lower()).strip()

def get_col(frame, *names):
    lookup = {norm(c): c for c in frame.columns}
    for name in names:
        if norm(name) in lookup:
            return lookup[norm(name)]
    raise ValueError(f"Missing column {names}; available columns: {list(frame.columns)}")

def code(s, width):
    x = s.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return x.where(x.str.fullmatch(r"\d{1," + str(width) + r"}").fillna(False)).str.zfill(width)

def load_population(raw):
    """Read CBSA totals; exclude county components and metro divisions.

    Census CBSA-EST2025-ALLDATA has no SUMLEV field. STCOU is the
    state/county component identifier; totals have a zero or empty STCOU.
    MDIV distinguishes metropolitan divisions from full CBSA totals.
    """
    df = pd.read_csv(io.BytesIO(raw), encoding="latin-1", low_memory=False, dtype=str)
    cbsa_col = get_col(df, "CBSA")
    pop_col = get_col(df, "POPESTIMATE2025")
    name_col = get_col(df, "NAME")
    stcou_col = get_col(df, "STCOU")
    mdiv_col = get_col(df, "MDIV")

    stcou = df[stcou_col].astype("string").str.strip()
    mdiv = df[mdiv_col].astype("string").str.strip()
    # Census uses zero-filled or blank component identifiers for totals.
    is_total = stcou.isna() | stcou.eq("") | stcou.str.fullmatch(r"0+", na=False)
    is_full_cbsa = mdiv.isna() | mdiv.eq("") | mdiv.str.fullmatch(r"0+", na=False)
    rows = df.loc[is_total & is_full_cbsa].copy()
    rows["cbsa_code"] = code(rows[cbsa_col], 5)
    rows["population_2025"] = pd.to_numeric(
        rows[pop_col].str.replace(",", "", regex=False), errors="coerce"
    )
    rows["population_name"] = rows[name_col].astype(str)
    rows = rows.dropna(subset=["cbsa_code", "population_2025"])
    if rows["cbsa_code"].duplicated().any():
        raise ValueError("Duplicate CBSA total records; inspect STCOU and MDIV filters")
    if len(rows) < 100:
        raise ValueError(
            f"Only {len(rows)} CBSA totals found; inspect STCOU/MDIV values: "
            f"STCOU={df[stcou_col].dropna().unique()[:8]}, "
            f"MDIV={df[mdiv_col].dropna().unique()[:8]}"
        )
    return rows[["cbsa_code", "population_2025", "population_name"]]

def load_delineation(raw):
    book = pd.ExcelFile(io.BytesIO(raw))
    for sheet in book.sheet_names:
        for header in range(12):
            df = pd.read_excel(book, sheet_name=sheet, header=header, dtype=str)
            try:
                cols = {
                    "cbsa": get_col(df, "CBSA Code"),
                    "title": get_col(df, "CBSA Title"),
                    "type": get_col(df, "Metropolitan/Micropolitan Statistical Area"),
                    "state": get_col(df, "FIPS State Code"),
                    "county": get_col(df, "FIPS County Code"),
                    "county_name": get_col(df, "County/County Equivalent"),
                    "state_name": get_col(df, "State Name"),
                }
                return df, cols
            except ValueError:
                continue
    raise ValueError("Cannot locate official delineation columns in List 1 workbook.")

def build(pop_bytes, delineation_bytes, count=100):
    pop = load_population(pop_bytes)
    raw, cols = load_delineation(delineation_bytes)
    geo = pd.DataFrame({
        "cbsa_code": code(raw[cols["cbsa"]], 5),
        "metro_title": raw[cols["title"]].astype("string").str.strip(),
        "metro_type": raw[cols["type"]].astype("string").str.strip(),
        "state_fips": code(raw[cols["state"]], 2),
        "county_code": code(raw[cols["county"]], 3),
        "county_name": raw[cols["county_name"]].astype("string").str.strip(),
        "state_name": raw[cols["state_name"]].astype("string").str.strip(),
    }).dropna(subset=["cbsa_code", "state_fips", "county_code"])
    geo = geo[geo.metro_type.str.contains("Metropolitan", case=False, na=False)].copy()
    geo["county_fips"] = geo.state_fips + geo.county_code
    geo = geo.drop_duplicates(["cbsa_code", "county_fips"])
    metro_titles = geo.groupby("cbsa_code")["metro_title"].first().rename("metro_title")
    metros = pop.merge(metro_titles, on="cbsa_code", how="inner")
    metros = metros.sort_values(["population_2025", "cbsa_code"], ascending=[False, True]).head(count).copy()
    if len(metros) != count:
        raise ValueError(f"Expected {count} metros, got {len(metros)}")
    metros["population_rank"] = range(1, count+1)
    metros["metro_key"] = metros.cbsa_code.map(lambda c: EXISTING.get(c, f"cbsa_{c}"))
    # Official CBSA title contains city and trailing state abbreviations.
    split = metros.metro_title.str.rsplit(", ", n=1, expand=True)
    if split.shape[1] != 2 or split[1].isna().any():
        raise ValueError("Unexpected official metro title format; cannot extract state abbreviations")
    metros["metro_name"] = split[0].str.strip()
    metros["states"] = split[1].str.strip()
    counties = geo.merge(metros[["cbsa_code", "metro_key"]], on="cbsa_code",
                         how="inner", validate="many_to_one")
    if counties.metro_key.nunique() != count:
        raise ValueError("County coverage missing for one or more selected metros")
    if counties.county_fips.duplicated().any():
        dups = counties[counties.county_fips.duplicated(keep=False)]
        raise ValueError(f"County assigned to multiple metros: {dups.county_fips.unique()[:8]}")
    if not counties.county_fips.str.fullmatch(r"\d{5}").all():
        raise ValueError("Invalid county FIPS")
    metros = metros[["metro_key", "cbsa_code", "metro_name", "states",
                     "population_rank", "population_2025"]].sort_values("population_rank")
    counties = counties[["metro_key", "cbsa_code", "metro_title", "county_fips",
                         "county_name", "state_name"]].sort_values(["metro_key", "county_fips"])
    return metros, counties

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--population-file", type=Path, help="Use locally downloaded Census CSV")
    p.add_argument("--delineation-file", type=Path, help="Use locally downloaded Census XLSX")
    p.add_argument("--registry", type=Path, default=Path("geography_registry"))
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--force", action="store_true", help="Overwrite existing registry CSVs")
    args = p.parse_args()
    if not 1 <= args.count <= 300:
        p.error("--count must be between 1 and 300")
    print("Reading Census 2025 metro population estimates...")
    pop = fetch(POP_URL, args.population_file)
    print("Reading official July 2023 MSA county delineations...")
    delineation = fetch(DELINEATION_URL, args.delineation_file)
    metros, counties = build(pop, delineation, args.count)
    args.registry.mkdir(parents=True, exist_ok=True)
    outputs = [(args.registry/"metros.csv", metros),
               (args.registry/"metro_counties.csv", counties)]
    existing = [str(path) for path, _ in outputs if path.exists()]
    if existing and not args.force:
        raise FileExistsError(f"Would overwrite {existing}; back up files and rerun with --force")
    for path, frame in outputs:
        frame.to_csv(path, index=False)
        print(f"Wrote {path}: {len(frame):,} rows")
    print(f"Verified: {metros.metro_key.nunique()} metros; {counties.county_fips.nunique()} unique counties.")
    print(metros.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
