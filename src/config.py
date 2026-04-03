"""Konfiguration — alle APIs kostenlos, kein Key nötig."""

class Settings:
    gleif_base_url: str = "https://api.gleif.org/api/v1"
    vies_base_url: str = "https://ec.europa.eu/taxation_customs/vies/rest-api"
    eurostat_base_url: str = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    # EU Consolidated Sanctions List (Finanzielle Sanktionen)
    eu_sanctions_url: str = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"
    # Insolvenzbekanntmachungen (Deutschland: insolvenzbekanntmachungen.de)
    insolvency_de_url: str = "https://www.insolvenzbekanntmachungen.de"
    # OpenSanctions API (gratis, kein Key für Basis-Abfragen)
    opensanctions_url: str = "https://api.opensanctions.org"
    http_timeout: float = 30.0

settings = Settings()
