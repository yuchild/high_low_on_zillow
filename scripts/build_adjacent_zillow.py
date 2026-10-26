"""Build Zillow county pool for neighbors not present in official top-100 metro data."""
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_target_metro_counties import build_dataset, DATASETS
from build_target_metro_kpis import build_kpis

REG=ROOT/'geography_registry'
PROCESSED=ROOT/'data/processed'

def main():
    expanded=pd.read_csv(REG/'metro_expanded_counties.csv',dtype={'county_fips':str})
    official=pd.read_csv(REG/'metro_counties.csv',dtype={'county_fips':str})
    missing=sorted(set(expanded.county_fips)-set(official.county_fips))
    if not missing:
        print('No additional county identifiers needed'); return
    pool=pd.DataFrame({'metro_key':'__adjacent__','county_fips':missing})
    for key,conf in DATASETS.items():
        output=f'adjacent_pool_{conf["output"]}'
        build_dataset({**conf,'output':output},pool)
        build_kpis({'file':output,'value':conf['value_col'],
                    'output':f'adjacent_pool_{"home_price" if key=="home_prices" else "rental"}_kpis.parquet'})
    print('Expanded pool built. Commit new adjacent_pool_*.parquet files for deployment.')

if __name__=='__main__': main()
