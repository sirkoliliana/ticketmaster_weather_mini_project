import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.database import get_db, Base
from app.models import EventWeatherRecord

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@test_db:5432/event_weather_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_search_events_empty_cache_fetches_from_api(mocker, client, test_db):
    # "mocker" is a pytest-mock fixture — just add it as a parameter, no imports needed
    mocker.patch("app.main.geocode_city", return_value=("52.2297", "21.0122"))
    mocker.patch("app.main.fetch_events", return_value=[{
        "name": "Test Concert",
        "url": "http://ticketmaster.test",
        "_embedded": {
            "venues": [{
                "location": {"latitude": "52.2297", "longitude": "21.0122"},
                "city": {"name": "Warsaw"},
                "address": {"line1": "123 Test St"}
            }]
        },
        "dates": {"start": {"localDate": "2026-06-05", "localTime": "20:00:00"}},
        "priceRanges": [{"min": 50.0, "max": 100.0, "currency": "PLN"}],
        "classifications": [{"segment": {"name": "Music"}, "genre": {"name": "Rock"}}]
    }])
    mocker.patch("app.main.fetch_weather", return_value={
        "weathercode": [0],
        "temperature_2m_max": [25.5],
        "temperature_2m_min": [15.0],
        "precipitation_probability_max": [10],
        "precipitation_sum": [0.0],
        "windspeed_10m_max": [12.5]
    })

    response = client.get(
        "/api/search?city=Warsaw&radius=30&start_date=2026-06-05&end_date=2026-06-05"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["event_name"] == "Test Concert"
    assert data["data"][0]["weather_condition"] == "Clear"

    saved_records = test_db.query(EventWeatherRecord).all()
    assert len(saved_records) == 1
    assert saved_records[0].city == "Warsaw"


def test_search_events_uses_cache(mocker, client, test_db):
    mocker.patch("app.main.geocode_city", return_value=("52.2", "21.0"))
    mock_events = mocker.patch("app.main.fetch_events")
    mock_weather = mocker.patch("app.main.fetch_weather")

    cached_event = EventWeatherRecord(
        event_name="Cached Show",
        city="Warsaw",
        target_date="2026-06-05",
        time="19:00:00",
        latitude="52.2",
        longitude="21.0"
    )
    test_db.add(cached_event)
    test_db.commit()

    response = client.get(
        "/api/search?city=Warsaw&radius=30&start_date=2026-06-05&end_date=2026-06-05"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["event_name"] == "Cached Show"

    mock_events.assert_not_called()
    mock_weather.assert_not_called()
