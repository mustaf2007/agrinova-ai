"""Evidence checks for comparing farm observations with ECOCROP species ranges.

This module deliberately avoids a composite suitability score. Time windows,
spatial resolution and measurement methods must be compatible before stronger
claims can be made.
"""
from __future__ import annotations

import math


def _number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _range_status(value, lower, upper):
    observed, low, high = _number(value), _number(lower), _number(upper)
    if observed is None or low is None or high is None or low > high:
        return "Not assessed"
    return "Within reference range" if low <= observed <= high else "Outside reference range"


def assess_crop_environment(record: dict | None, mean_temperature_c=None, soil_ph=None) -> list[dict]:
    """Return indicator-level comparisons, never an overall crop suitability score."""
    if not record:
        return []
    results = []
    temperature_status = _range_status(mean_temperature_c, record.get("topmn"), record.get("topmx"))
    results.append({
        "Indicator": "Observed mean temperature",
        "Observation": f"{_number(mean_temperature_c):.1f} °C" if _number(mean_temperature_c) is not None else "Not available",
        "ECOCROP reference": "Optimal range: " + (
            f"{_number(record.get('topmn')):g} to {_number(record.get('topmx')):g} °C"
            if _number(record.get("topmn")) is not None and _number(record.get("topmx")) is not None
            else "Not available"
        ),
        "Comparison": temperature_status,
        "Interpretation": "A short historical mean is contextual evidence only; it does not establish seasonal or crop-cycle suitability.",
    })
    ph_status = _range_status(soil_ph, record.get("phmin"), record.get("phmax"))
    results.append({
        "Indicator": "Reported soil pH",
        "Observation": f"{_number(soil_ph):.1f}" if _number(soil_ph) is not None else "Not supplied",
        "ECOCROP reference": "Absolute range: " + (
            f"{_number(record.get('phmin')):g} to {_number(record.get('phmax')):g}"
            if _number(record.get("phmin")) is not None and _number(record.get("phmax")) is not None
            else "Not available"
        ),
        "Comparison": ph_status,
        "Interpretation": "Compare only after confirming the soil test method and representative sampling.",
    })
    return results


def normalize_spatial_observations(
    frame,
    latitude_column: str,
    longitude_column: str,
    temperature_column: str | None = None,
    soil_ph_column: str | None = None,
):
    """Validate user-supplied point observations for mapping.

    Coordinates are required; environmental measurements are optional. This
    does not sample raster cells or infer values from coordinates.
    """
    import pandas as pd

    if frame is None or frame.empty:
        return pd.DataFrame(), ["The uploaded dataset is empty."]
    if latitude_column not in frame.columns or longitude_column not in frame.columns:
        return pd.DataFrame(), ["Select valid latitude and longitude columns."]
    output = pd.DataFrame(index=frame.index)
    output["latitude"] = pd.to_numeric(frame[latitude_column], errors="coerce")
    output["longitude"] = pd.to_numeric(frame[longitude_column], errors="coerce")
    invalid_coordinates = (
        output["latitude"].isna()
        | output["longitude"].isna()
        | ~output["latitude"].between(-90, 90)
        | ~output["longitude"].between(-180, 180)
    )
    output["source_row"] = range(2, len(output) + 2)
    if temperature_column and temperature_column in frame.columns:
        output["mean_temperature_c"] = pd.to_numeric(frame[temperature_column], errors="coerce")
    if soil_ph_column and soil_ph_column in frame.columns:
        ph = pd.to_numeric(frame[soil_ph_column], errors="coerce")
        output["soil_ph"] = ph.where(ph.between(0, 14))
    output = output.loc[~invalid_coordinates].copy().reset_index(drop=True)
    warnings = []
    dropped = int(invalid_coordinates.sum())
    if dropped:
        warnings.append(f"{dropped} row(s) with missing or out-of-range coordinates were excluded.")
    if output.empty:
        warnings.append("No valid coordinate records remain.")
    return output, warnings
