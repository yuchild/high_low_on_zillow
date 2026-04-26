import pandas as pd

from high_low_on_zillow.geo.county_geo import add_county_fips


def test_add_county_fips_for_bay_area_counties():
    df = pd.DataFrame(
        {
            "county": [
                "Alameda",
                "Contra Costa",
                "Marin",
                "Napa",
                "San Francisco",
                "San Mateo",
                "Santa Clara",
                "Solano",
                "Sonoma",
            ]
        }
    )

    out = add_county_fips(df)

    assert out["fips"].notna().all()
    assert out.loc[out["county"] == "San Francisco", "fips"].iloc[0] == "06075"
    assert out.loc[out["county"] == "Santa Clara", "fips"].iloc[0] == "06085"