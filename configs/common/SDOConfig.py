"""Shared, fail-closed configuration helpers for SDO."""


def is_sdo_enabled(options):
    """Return true only for the exact, explicitly selected SDO scheme."""

    return getattr(options, "scheme", None) == "SDO"
