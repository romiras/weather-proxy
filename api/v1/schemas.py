from pydantic import BaseModel
from typing import List

class ForecastItem(BaseModel):
    time: str
    temperature: float
    
class WeatherResponse(BaseModel):
    city_name: str
    current_temperature: float
    current_humidity: float
    hourly_forecast: List[ForecastItem]
