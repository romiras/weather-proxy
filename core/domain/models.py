from dataclasses import dataclass
from typing import List

@dataclass
class WeatherEntity:
    city: str
    temperature: float
    humidity: float
    forecast: List[dict]  # List of dictionaries for next 5 hours
