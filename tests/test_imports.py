from high_low_on_zillow.config import get_settings, get_data_sources


def test_config_loads():
    settings = get_settings()
    sources = get_data_sources()

    assert settings["project"]["name"] == "high_low_on_zillow"
    assert sources["zillow_research"]["enabled"] is True