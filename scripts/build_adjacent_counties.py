"""Build first-ring county neighbors from local county GeoJSON; no external GIS service."""
import json
from pathlib import Path
import pandas as pd
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'geography_registry'
GEO = ROOT / 'data/external/geojson-counties-fips.json'

def build():
    official = pd.read_csv(REG/'metro_counties.csv', dtype={'county_fips':str,'metro_key':str})
    official['county_fips'] = official['county_fips'].str.zfill(5)
    with GEO.open() as fh: data=json.load(fh)
    geoms, fips = [], []
    for feat in data['features']:
        code=str(feat.get('id','')).zfill(5)
        if len(code)==5 and code.isdigit() and feat.get('geometry'):
            geom=shape(feat['geometry'])
            if not geom.is_empty:
                geoms.append(geom); fips.append(code)
    if len(fips)!=len(set(fips)): raise ValueError('Duplicate FIPS in GeoJSON')
    idx={code:i for i,code in enumerate(fips)}
    tree=STRtree(geoms)
    records=[]
    missing=set(official.county_fips)-set(fips)
    if missing: print('Official counties missing from map geometry:', ', '.join(sorted(missing)))
    for metro, group in official.groupby('metro_key',sort=False):
        core=set(group.county_fips)
        neighbors=set()
        for code in core & idx.keys():
            geom=geoms[idx[code]]
            # Shared boundary (not just a single vertex); use a small tolerance for
            # GeoJSON simplification differences. Geographic units are degrees.
            for j in tree.query(geom.buffer(0.001)):
                other=fips[int(j)]
                if other in core or other==code: continue
                candidate=geoms[int(j)]
                shared=geom.boundary.intersection(candidate.boundary.buffer(0.001))
                if shared.length > 0.01:
                    neighbors.add(other)
        records.extend((metro, code, 0, 'official') for code in sorted(core))
        records.extend((metro, code, 1, 'adjacent') for code in sorted(neighbors))
    result=pd.DataFrame(records,columns=['metro_key','county_fips','ring_distance','coverage_type'])
    if result.duplicated(['metro_key','county_fips']).any(): raise ValueError('Duplicate metro/county membership')
    result.to_csv(REG/'metro_expanded_counties.csv',index=False)
    print(f'Wrote {len(result):,} memberships; {result.county_fips.nunique():,} unique counties; {len(result.query("ring_distance == 1")):,} adjacent memberships')
    print('Note: adjacency derived from simplified GeoJSON; inspect coastal/river boundaries before treating as authoritative.')

if __name__=='__main__': build()
