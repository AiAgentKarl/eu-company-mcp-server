"""Konfiguration — alle APIs kostenlos, kein Key nötig."""

class Settings:
    gleif_base_url: str = "https://api.gleif.org/api/v1"
    vies_base_url: str = "https://ec.europa.eu/taxation_customs/vies/rest-api"
    eurostat_base_url: str = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    http_timeout: float = 30.0

settings = Settings()
