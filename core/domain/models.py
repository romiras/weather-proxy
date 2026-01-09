from dataclasses import dataclass


@dataclass
class WeatherEntity:
    city: str
    temperature: float
    humidity: float
    forecast: list[dict]  # List of dictionaries for next 5 hours
