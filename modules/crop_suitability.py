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
    warnings = []
    if temperature_column and temperature_column in frame.columns:
        temperature = pd.to_numeric(frame[temperature_column], errors="coerce")
        output["mean_temperature_c"] = temperature
        invalid_temperature = frame[temperature_column].notna() & temperature.isna()
        if invalid_temperature.any():
            warnings.append(f"{int(invalid_temperature.sum())} non-numeric temperature value(s) were left unavailable.")
    if soil_ph_column and soil_ph_column in frame.columns:
        ph = pd.to_numeric(frame[soil_ph_column], errors="coerce")
        invalid_ph = ph.notna() & ~ph.between(0, 14)
        output["soil_ph"] = ph.where(ph.between(0, 14))
        if invalid_ph.any():
            warnings.append(f"{int(invalid_ph.sum())} soil pH value(s) outside 0–14 were left unavailable.")
    output = output.loc[~invalid_coordinates].copy().reset_index(drop=True)
    dropped = int(invalid_coordinates.sum())
    if dropped:
        warnings.append(f"{dropped} row(s) with missing or out-of-range coordinates were excluded.")
    if output.empty:
        warnings.append("No valid coordinate records remain.")
    return output, warnings



def validate_geojson_boundaries(data):
    """Validate Polygon/MultiPolygon GeoJSON for boundary visualisation.

    This validates coordinate structure and geographic bounds only. It does
    not repair topology, verify ownership, or assess agricultural suitability.
    """
    import copy

    if not isinstance(data, dict):
        return None, ["GeoJSON must be a JSON object."], None
    kind = data.get("type")
    if kind == "FeatureCollection":
        features = data.get("features")
    elif kind == "Feature":
        features = [data]
    elif kind in {"Polygon", "MultiPolygon"}:
        features = [{"type": "Feature", "properties": {}, "geometry": data}]
    else:
        return None, ["Provide a GeoJSON Feature, FeatureCollection, Polygon or MultiPolygon."], None
    if not isinstance(features, list) or not features:
        return None, ["The GeoJSON contains no features."], None

    accepted = []
    all_lons, all_lats = [], []
    warnings = []

    def validate_ring(ring):
        if not isinstance(ring, list) or len(ring) < 4:
            return False
        points = []
        for coordinate in ring:
            if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
                return False
            try:
                lon, lat = float(coordinate[0]), float(coordinate[1])
            except (TypeError, ValueError):
                return False
            if not math.isfinite(lon) or not math.isfinite(lat):
                return False
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                return False
            points.append((lon, lat))
        if points[0] != points[-1]:
            return False
        return points

    for index, feature in enumerate(features):
        geometry = feature.get("geometry") if isinstance(feature, dict) and feature.get("type") == "Feature" else None
        if not isinstance(geometry, dict):
            warnings.append(f"Feature {index + 1}: missing or invalid geometry; skipped.")
            continue
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        polygons = [coordinates] if geometry_type == "Polygon" else coordinates if geometry_type == "MultiPolygon" else None
        if not isinstance(polygons, list) or not polygons:
            warnings.append(f"Feature {index + 1}: only Polygon and MultiPolygon geometries are supported; skipped.")
            continue
        feature_points = []
        valid = True
        for polygon in polygons:
            if not isinstance(polygon, list) or not polygon:
                valid = False
                break
            for ring in polygon:
                points = validate_ring(ring)
                if not points:
                    valid = False
                    break
                feature_points.extend(points)
            if not valid:
                break
        if not valid:
            warnings.append(f"Feature {index + 1}: invalid ring, unclosed boundary, or out-of-range coordinate; skipped.")
            continue
        all_lons.extend(point[0] for point in feature_points)
        all_lats.extend(point[1] for point in feature_points)
        accepted.append(copy.deepcopy(feature))

    if not accepted:
        return None, warnings or ["No valid polygon boundaries were found."], None
    output = {"type": "FeatureCollection", "features": accepted}
    bounds = [[min(all_lats), min(all_lons)], [max(all_lats), max(all_lons)]]
    return output, warnings, bounds
