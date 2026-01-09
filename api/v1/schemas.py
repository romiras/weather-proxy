from pydantic import BaseModel


class ForecastItem(BaseModel):
    time: str
    temperature: float


class WeatherResponse(BaseModel):
    city_name: str
    current_temperature: float
    current_humidity: float
    hourly_forecast: list[ForecastItem]
