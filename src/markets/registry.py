"""
Market-entity derivation registry. Metro derivation is deliberately
NOT wired in here yet — src/markets/galway/metro.py is a stub pending
the 2026-06-25 commuter-shed discussion's open questions (spec section 10).
"""

from src.markets.galway.city import is_galway_city
from src.markets.galway.county import is_galway_county


def derive_market_entities(application) -> list[str]:
    entities: list[str] = []
    if is_galway_city(application.planning_authority):
        entities.append("GALWAY_CITY")
    if is_galway_county(application.planning_authority):
        entities.append("GALWAY_COUNTY")
    return entities
