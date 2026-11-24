"""Small, auditable SoilGrids WCS discovery helpers.

The REST point-query API is not used. This module reads WCS GetCapabilities
metadata from the documented ISRIC nitrogen service only; it does not download
or interpret raster pixels.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

SOILGRIDS_NITROGEN_WCS = "https://maps.isric.org/mapserv?map=/map/nitrogen.map"
SOILGRIDS_WCS_DOCS = "https://docs.isric.org/globaldata/soilgrids/wcs.html"


def parse_wcs_coverages(xml_text: str) -> list[str]:
    """Extract advertised coverage identifiers from a WCS capabilities XML."""
    if not isinstance(xml_text, str) or not xml_text.strip():
        raise ValueError("The WCS capabilities response is empty.")
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError("The WCS service did not return valid XML capabilities.") from exc
    identifiers = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].lower() in {"coverageid", "identifier"}:
            value = (element.text or "").strip()
            if value and value not in identifiers:
                identifiers.append(value)
    if not identifiers:
        raise ValueError("No coverage identifiers were advertised by this WCS response.")
    return identifiers


def fetch_nitrogen_coverages(timeout: int = 15) -> list[str]:
    """Fetch current nitrogen coverage metadata from the official ISRIC WCS."""
    response = requests.get(
        SOILGRIDS_NITROGEN_WCS,
        params={
            "SERVICE": "WCS",
            "VERSION": "2.0.0",
            "REQUEST": "GetCapabilities",
        },
        timeout=timeout,
        headers={"User-Agent": "AgriNova-AI/1.0 (SoilGrids WCS metadata discovery)"},
    )
    response.raise_for_status()
    return parse_wcs_coverages(response.text)
