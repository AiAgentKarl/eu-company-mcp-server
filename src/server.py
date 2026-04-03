"""EU Company MCP Server — Firmendaten, Compliance, Sanktionen, EU-Wirtschaftsstatistiken.

5 kostenlose Datenquellen:
- GLEIF (Firmensuche, LEI, Konzernstrukturen — 2M+ Unternehmen weltweit)
- VIES (EU USt-ID Validierung)
- Eurostat (BIP, Arbeitsmarkt, Inflation, Unternehmensdemografie, Branchenstatistiken)
- OpenSanctions (EU/US/UN Sanktionslisten, Beneficial Ownership)
- Insolvenzbekanntmachungen.de + EU E-Justice Portal
"""

from mcp.server.fastmcp import FastMCP

from src.tools.company import register_company_tools
from src.tools.vat import register_vat_tools
from src.tools.statistics import register_statistics_tools
from src.tools.compliance import register_compliance_tools

mcp = FastMCP(
    "EU Company MCP Server",
    instructions=(
        "Provides AI agents with EU company and business data: "
        "company search (GLEIF/LEI), corporate structures, "
        "VAT validation (VIES), EU economic statistics (Eurostat), "
        "insolvency search, beneficial ownership lookup, "
        "sanctions screening (EU/US/UN), and industry statistics."
    ),
)

register_company_tools(mcp)
register_vat_tools(mcp)
register_statistics_tools(mcp)
register_compliance_tools(mcp)

def main():
    """Server starten."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
