class CityNotFound(Exception):
    """Raised when a city cannot be found by the geocoding provider."""
    def __init__(self, city_name: str):
        self.city_name = city_name
        super().__init__(f"City '{city_name}' not found.")
