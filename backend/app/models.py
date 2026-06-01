from sqlalchemy import Column, Integer, String, Float, Date, Time
from app.database import Base

class EventWeatherRecord(Base):
    __tablename__ = "event_weather_records"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, index=True)
    city = Column(String, index=True)
    address = Column(String, nullable=True)
    target_date = Column(Date)
    time = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    ticket_url = Column(String, nullable=True)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    segment = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    weather_temp_max = Column(Float, nullable=True)
    weather_temp_min = Column(Float, nullable=True)
    weather_precip_prob_pct = Column(Float, nullable=True)
    weather_precip_mm = Column(Float, nullable=True)
    weather_wind_speed_kmh = Column(Float, nullable=True)
    weather_condition = Column(String, nullable=True)
