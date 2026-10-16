# Nationwide geographic registry (Step 2A)

`target_cities.csv` records the 18 requested city labels. Dallas and Fort Worth intentionally share the `dallas_fort_worth` metro key, yielding 17 unique metro keys. `cbsa_code` is intentionally blank until verified against the current official metropolitan delineation.

`metro_counties.csv` is a schema-only file: populate it from the official OMB/Census metropolitan statistical area county delineation crosswalk. Do not infer county membership from a city's county, and do not join county data by name alone. Preserve five-character zero-padded county FIPS and five-character CBSA codes as strings.

This is a staging registry, not a verified metropolitan crosswalk. Do not enable it in production processing until identifiers, metro definitions, and coverage are validated.
