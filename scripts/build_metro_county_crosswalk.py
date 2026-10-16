"""Build a verified metro-to-county registry from Census/OMB July 2023 List 1.

Run from the repository root:
  python scripts/build_metro_county_crosswalk.py --source data/external/list1_2023.xlsx

Download the official List 1 XLSX from:
https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import pandas as pd

CBSA_BY_KEY = {
    'new_york': '35620', 'los_angeles': '31080', 'chicago': '16980',
    'houston': '26420', 'phoenix': '38060', 'philadelphia': '37980',
    'san_antonio': '41700', 'san_diego': '41740',
    'dallas_fort_worth': '19100', 'jacksonville': '27260',
    'austin': '12420', 'charlotte': '16740', 'columbus': '18140',
    'indianapolis': '26900', 'seattle': '42660', 'denver': '19740',
    'oklahoma_city': '36420',
}


def normalized(value: object) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', str(value).lower()).strip()


def identify_columns(frame: pd.DataFrame) -> dict[str, str] | None:
    columns = {normalized(c): c for c in frame.columns}
    rules = {
        'cbsa': lambda n: n in {'cbsa code', 'cbsa'},
        'state_fips': lambda n: n in {'fips state code', 'state fips code'},
        'county_fips': lambda n: n in {'fips county code', 'county fips code'},
        'county': lambda n: 'county county equivalent' in n or n == 'county name',
        'state': lambda n: n in {'state name', 'state'},
        'metro_title': lambda n: n in {'cbsa title', 'metropolitan statistical area title'},
        'type': lambda n: 'metropolitan micropolitan statistical area' in n,
    }
    found = {}
    for key, predicate in rules.items():
        match = next((original for n, original in columns.items() if predicate(n)), None)
        if match is not None:
            found[key] = match
    required = {'cbsa', 'state_fips', 'county_fips', 'county', 'state'}
    return found if required.issubset(found) else None


def read_delineation(source: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    book = pd.ExcelFile(source)
    for sheet in book.sheet_names:
        for header_row in range(0, 12):
            frame = pd.read_excel(book, sheet_name=sheet, header=header_row, dtype=str)
            columns = identify_columns(frame)
            if columns:
                return frame, columns
    raise ValueError('Could not identify Census List 1 columns. Check the source workbook.')


def fips_part(series: pd.Series, digits: int) -> pd.Series:
    clean = series.astype('string').str.strip().str.replace(r'\.0$', '', regex=True)
    valid = clean.str.fullmatch(r'\d{1,' + str(digits) + r'}').fillna(False)
    return clean.where(valid).str.zfill(digits)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--registry', type=Path, default=Path('geography_registry'))
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f'Official delineation workbook not found: {args.source}')

    cities_path = args.registry / 'target_cities.csv'
    cities = pd.read_csv(cities_path, dtype=str, keep_default_na=False)
    if len(cities) != 18 or set(cities.metro_key) != set(CBSA_BY_KEY):
        raise ValueError('Unexpected target city registry; review changes before proceeding.')

    raw, cols = read_delineation(args.source)
    df = pd.DataFrame({
        'cbsa_code': fips_part(raw[cols['cbsa']], 5),
        'state_fips': fips_part(raw[cols['state_fips']], 2),
        'county_code': fips_part(raw[cols['county_fips']], 3),
        'county_name': raw[cols['county']].astype('string').str.strip(),
        'state_name': raw[cols['state']].astype('string').str.strip(),
    })
    if 'metro_title' in cols:
        df['metro_name'] = raw[cols['metro_title']].astype('string').str.strip()
    else:
        df['metro_name'] = ''
    df = df.dropna(subset=['cbsa_code', 'state_fips', 'county_code'])
    df['county_fips'] = df.state_fips + df.county_code
    mapping = pd.DataFrame([{'metro_key': k, 'cbsa_code': v} for k, v in CBSA_BY_KEY.items()])
    result = mapping.merge(df, on='cbsa_code', how='left', validate='one_to_many')
    missing = result.loc[result.county_fips.isna(), 'metro_key'].unique().tolist()
    if missing:
        raise ValueError(f'CBSAs not found in official delineation file: {missing}')

    result = result[['metro_key', 'cbsa_code', 'metro_name', 'county_fips', 'county_name', 'state_name']]
    result = result.drop_duplicates(subset=['metro_key', 'county_fips'])
    if not result.county_fips.str.fullmatch(r'\d{5}').all():
        raise ValueError('Invalid five-digit county FIPS found.')
    if result.groupby('metro_key').county_fips.nunique().size != 17:
        raise ValueError('Expected county coverage for all 17 metros.')
    if result.duplicated(['metro_key', 'county_fips']).any():
        raise ValueError('Duplicate county membership within a metro.')

    # Ensure all rows with a CBSA code have a consistent official title.
    for cbsa, group in result.groupby('cbsa_code'):
        titles = group.metro_name.dropna().loc[lambda s: s.ne('')].unique()
        if len(titles) > 1:
            raise ValueError(f'Inconsistent official names for CBSA {cbsa}: {titles}')

    cities['cbsa_code'] = cities.metro_key.map(CBSA_BY_KEY)
    cities['verification_status'] = 'matched_census_2023_delineation'
    result = result.sort_values(['metro_key', 'county_fips']).reset_index(drop=True)
    # Write only after all validations pass.
    result.to_csv(args.registry / 'metro_counties.csv', index=False)
    cities.to_csv(cities_path, index=False)
    print(f'Cities: {len(cities)}')
    print(f'Unique metros: {cities.cbsa_code.nunique()}')
    print(f'Metro-county memberships: {len(result)}')
    print(result.groupby(['metro_key', 'cbsa_code']).county_fips.nunique().to_string())
    print('Crosswalk saved:', args.registry / 'metro_counties.csv')


if __name__ == '__main__':
    main()
