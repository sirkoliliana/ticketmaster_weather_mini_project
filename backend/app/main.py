from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date
from app.ingestion import geocode_city, fetch_events, fetch_weather
from app.database import engine, get_db, Base
from app.models import EventWeatherRecord

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event-Weather API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WMO_CODES = {
    0: "Clear", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 53: "Drizzle", 55: "Heavy Drizzle",
    61: "Light Rain", 63: "Rain", 65: "Heavy Rain", 71: "Light Snow", 73: "Snow", 75: "Heavy Snow",
    80: "Rain Showers", 81: "Heavy Rain Showers", 82: "Violent Rain Showers",
    95: "Thunderstorm", 96: "Thunderstorm + Hail", 99: "Heavy Thunderstorm"
}


@app.get("/api/search")
def search_events(
    city: str,
    radius: int = 30,
    start_date: str = Query(default_factory=lambda: date.today().isoformat()),
    end_date: str = Query(default_factory=lambda: date.today().isoformat()),
    db: Session = Depends(get_db)
):
    try:
        center_lat, center_lon = geocode_city(city)
    except ValueError:
        raise HTTPException(status_code=404, detail="City not found")
    except Exception:
        raise HTTPException(status_code=502, detail="External API error")

    # Fetch existing cache
    cached_records = db.query(EventWeatherRecord).filter(
        EventWeatherRecord.city.ilike(f"%{city}%"),
        EventWeatherRecord.target_date >= start_date,
        EventWeatherRecord.target_date <= end_date
    ).all()

    if cached_records:
        return {"center": {"lat": center_lat, "lon": center_lon}, "data": cached_records}

    # Fetch from APIs
    try:
        events = fetch_events(center_lat, center_lon, radius, start_date, end_date)
    except Exception:
        raise HTTPException(status_code=502, detail="External API error")

    if not events:
        return {"center": {"lat": center_lat, "lon": center_lon}, "data": []}

    results = []
    for event in events:
        try:
            venue = event["_embedded"]["venues"][0]
            lat = venue["location"]["latitude"]
            lon = venue["location"]["longitude"]
            city_name = venue.get("city", {}).get("name", "Unknown")
            
            event_date = event.get("dates", {}).get("start", {}).get("localDate")
            if not event_date:
                continue

            # Deduplication check
            existing = db.query(EventWeatherRecord).filter_by(
                event_name=event.get("name"),
                target_date=event_date,
                time=event.get("dates", {}).get("start", {}).get("localTime", "TBD")
            ).first()

            if existing:
                results.append(existing)
                continue

            weather = fetch_weather(lat, lon, event_date)
            wcode = weather.get("weathercode", [None])[0]
            prices = event.get("priceRanges", [{}])[0]
            classifications = event.get("classifications", [{}])[0]

            record_data = {
                "event_name": event.get("name"),
                "city": city_name,
                "target_date": event_date,
                "time": event.get("dates", {}).get("start", {}).get("localTime", "TBD"),
                "latitude": lat,
                "longitude": lon,
                "ticket_url": event.get("url"),
                "price_min": prices.get("min"),
                "price_max": prices.get("max"),
                "currency": prices.get("currency"),
                "segment": classifications.get("segment", {}).get("name"),
                "genre": classifications.get("genre", {}).get("name"),
                "weather_temp_max": weather.get("temperature_2m_max", [None])[0],
                "weather_temp_min": weather.get("temperature_2m_min", [None])[0],
                "weather_precip_prob_pct": weather.get("precipitation_probability_max", [None])[0],
                "weather_precip_mm": weather.get("precipitation_sum", [None])[0],
                "weather_wind_speed_kmh": weather.get("windspeed_10m_max", [None])[0],
                "weather_condition": WMO_CODES.get(wcode, "Unknown")
            }

            db_record = EventWeatherRecord(**record_data)
            db.add(db_record)
            results.append(db_record)
            
        except (KeyError, IndexError):
            continue

    db.commit()
    return {"center": {"lat": center_lat, "lon": center_lon}, "data": results}
