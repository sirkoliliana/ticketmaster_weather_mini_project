import pytest
from unittest.mock import patch, Mock
from app.ingestion import geocode_city

@patch("app.ingestion.requests.get")
def test_geocode_city_success(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [{"latitude": 52.2297, "longitude": 21.0122}]
    }
    mock_get.return_value = mock_response

    lat, lon = geocode_city("Warsaw")
    
    assert lat == "52.2297"
    assert lon == "21.0122"

@patch("app.ingestion.requests.get")
def test_geocode_city_not_found(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="City not found"):
        geocode_city("FakeCityXYZ")
