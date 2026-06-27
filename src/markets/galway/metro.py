# TODO: commuter-belt polygons pending — see docs/source-inventory.md and
# the 2026-06-25 commuter-shed discussion (membership rule, POWCAR data,
# partition vs. shared-belt). Candidate source: Galway County's open-data
# ArcGIS portal.
#
# Once resolved, this module should expose:
#   def is_in_galway_metro(application) -> bool
# using application.site_geometry against the commuter-belt polygon(s).


def is_in_galway_metro(application) -> bool:
    raise NotImplementedError(
        "Galway Metro commuter-belt derivation is not implemented yet — "
        "see the TODO at the top of this file."
    )
