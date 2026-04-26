from high_low_on_zillow.config import get_data_sources


def test_zillow_data_source_structure():
    sources = get_data_sources()
    zillow = sources["zillow_research"]

    assert zillow["enabled"] is True
    assert "datasets" in zillow
    assert "home_prices" in zillow["datasets"]
    assert "rentals" in zillow["datasets"]