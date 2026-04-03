"""Statistik-Tools — EU Wirtschaftsdaten (Eurostat)."""

from mcp.server.fastmcp import FastMCP
from src.clients.eurostat import EurostatClient

_eurostat = EurostatClient()


def _parse_eurostat_response(data: dict) -> list[dict]:
    """Eurostat JSON-stat 2.0 Response in lesbares Format umwandeln."""
    values = data.get("value", {})
    dimensions = data.get("dimension", {})
    sizes = data.get("size", [])

    if not values or not dimensions:
        return []

    # Dimension-Labels und Indices extrahieren
    dim_info = []
    for dim_id in data.get("id", []):
        dim = dimensions.get(dim_id, {})
        categories = dim.get("category", {})
        labels = categories.get("label", {})
        index = categories.get("index", {})
        # Index umkehren: position → code
        pos_to_code = {v: k for k, v in index.items()}
        dim_info.append({
            "id": dim_id,
            "label": dim.get("label", dim_id),
            "pos_to_code": pos_to_code,
            "code_to_label": labels,
            "size": len(index),
        })

    # Werte mit Dimensionen verknüpfen
    results = []
    for flat_idx_str, value in values.items():
        flat_idx = int(flat_idx_str)

        # Multi-dimensionalen Index berechnen
        entry = {"wert": value}
        remaining = flat_idx
        for i in range(len(dim_info) - 1, -1, -1):
            dim_size = dim_info[i]["size"]
            pos = remaining % dim_size
            remaining //= dim_size
            code = dim_info[i]["pos_to_code"].get(pos, str(pos))
            label = dim_info[i]["code_to_label"].get(code, code)
            entry[dim_info[i]["id"]] = label

        results.append(entry)

    return results


def register_statistics_tools(mcp: FastMCP):

    @mcp.tool()
    async def eu_gdp(
        countries: str = "DE;FR;IT;ES",
        years: str = "2022;2023",
    ) -> dict:
        """BIP (Bruttoinlandsprodukt) für EU-Länder abrufen.

        Quelle: Eurostat. Werte in Millionen Euro.

        Args:
            countries: Ländercodes mit Semikolon getrennt (z.B. "DE;FR;IT")
            years: Jahre mit Semikolon getrennt (z.B. "2022;2023")
        """
        country_list = [c.strip() for c in countries.split(";")]
        year_list = [y.strip() for y in years.split(";")]

        data = await _eurostat.get_gdp(country_list, year_list)
        results = _parse_eurostat_response(data)

        return {
            "indikator": "BIP (Bruttoinlandsprodukt)",
            "einheit": "Millionen EUR",
            "daten": results,
        }

    @mcp.tool()
    async def eu_unemployment(
        countries: str = "DE;FR;IT;ES",
        periods: str = "2025-01",
    ) -> dict:
        """Arbeitslosenquote für EU-Länder (monatlich, saisonbereinigt).

        Args:
            countries: Ländercodes (z.B. "DE;FR;IT")
            periods: Monate im Format YYYY-MM (z.B. "2025-01;2025-06")
        """
        country_list = [c.strip() for c in countries.split(";")]
        period_list = [p.strip() for p in periods.split(";")]

        data = await _eurostat.get_unemployment(country_list, period_list)
        results = _parse_eurostat_response(data)

        return {
            "indikator": "Arbeitslosenquote (saisonbereinigt)",
            "einheit": "Prozent",
            "daten": results,
        }

    @mcp.tool()
    async def eu_inflation(
        countries: str = "DE;FR;IT;ES",
        periods: str = "2025-01",
    ) -> dict:
        """Inflationsrate (HICP) für EU-Länder.

        Args:
            countries: Ländercodes (z.B. "DE;FR")
            periods: Monate im Format YYYY-MM (z.B. "2025-01;2025-06")
        """
        country_list = [c.strip() for c in countries.split(";")]
        period_list = [p.strip() for p in periods.split(";")]

        data = await _eurostat.get_inflation(country_list, period_list)
        results = _parse_eurostat_response(data)

        return {
            "indikator": "Inflation (HICP, Jahresrate)",
            "einheit": "Prozent",
            "daten": results,
        }

    @mcp.tool()
    async def eu_business_demography(
        countries: str = "DE;FR;IT;ES",
        year: str = "2021",
    ) -> dict:
        """Unternehmensdemografie: Gründungen, Schließungen, aktive Firmen.

        Zeigt wie viele Unternehmen gegründet/geschlossen wurden.
        Quelle: Eurostat.

        Args:
            countries: Ländercodes (z.B. "DE;FR;IT")
            year: Jahr (z.B. "2021")
        """
        country_list = [c.strip() for c in countries.split(";")]

        data = await _eurostat.get_business_demography(country_list, year)
        results = _parse_eurostat_response(data)

        return {
            "indikator": "Unternehmensdemografie",
            "jahr": year,
            "daten": results,
        }

    @mcp.tool()
    async def get_industry_statistics(
        country: str, industry_code: str = "C", year: str = "2021",
    ) -> dict:
        """Branchenstatistiken nach NACE-Code (EU-Wirtschaftsklassifikation).

        Gibt Anzahl Unternehmen, Umsatz und Beschäftigte für eine
        Branche in einem EU-Land zurück. Quelle: Eurostat SBS.

        Häufige NACE-Codes:
        - C = Verarbeitendes Gewerbe (Manufacturing)
        - G = Handel (Wholesale/Retail)
        - F = Baugewerbe (Construction)
        - J = IT/Kommunikation (Information/Communication)
        - K = Finanz/Versicherung (Financial Services)
        - M = Freiberufler/Wissenschaft (Professional/Scientific)
        - H = Verkehr/Lagerei (Transport/Storage)
        - I = Gastgewerbe (Accommodation/Food)
        - L = Immobilien (Real Estate)

        Args:
            country: ISO-Ländercode (z.B. "DE", "FR", "IT")
            industry_code: NACE Rev.2 Code (z.B. "C", "G47", "J62")
            year: Jahr (z.B. "2021")
        """
        data = await _eurostat.get_industry_statistics(
            countries=[country.upper()],
            nace_code=industry_code,
            year=year,
        )
        results = _parse_eurostat_response(data)

        return {
            "indikator": "Branchenstatistik (Structural Business Statistics)",
            "land": country.upper(),
            "nace_code": industry_code,
            "jahr": year,
            "kennzahlen": {
                "V11110": "Anzahl Unternehmen",
                "V12110": "Umsatz (Tsd. EUR)",
                "V16110": "Beschäftigte",
            },
            "daten": results,
        }
