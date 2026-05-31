import os
import requests
from typing import List, Dict, Any

TICKETMASTER_KEY = os.getenv("TICKETMASTER_API_KEY")

def geocode_city(city: str) -> tuple[str, str]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    response = requests.get(url, params={"name": city, "count": 1})
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise ValueError("City not found")
    return str(results[0]["latitude"]), str(results[0]["longitude"])

# UPDATED to accept date range
def fetch_events(lat: str, lon: str, radius: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    start_dt = f"{start_date}T00:00:00Z"
    end_dt = f"{end_date}T23:59:59Z"
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "latlong": f"{lat},{lon}",
        "radius": radius,
        "unit": "km",
        "startDateTime": start_dt,
        "endDateTime": end_dt,
        "size": 200,
        "apikey": TICKETMASTER_KEY,
        "sort": "date,asc"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("_embedded", {}).get("events", [])

def fetch_weather(lat: str, lon: str, target_date: str) -> Dict[str, Any]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": target_date,
        "end_date": target_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,windspeed_10m_max,weathercode",
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("daily", {})
