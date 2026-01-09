class CityNotFound(Exception):
    def __init__(self, city_name: str):
        super().__init__(f"City not found: {city_name}")

class ServiceUnavailable(Exception):
    def __init__(self, service_name: str):
        super().__init__(f"Service unavailable: {service_name}")
