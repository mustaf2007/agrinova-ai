"""Utilities for importing and validating user-provided soil laboratory data."""

from __future__ import annotations

import pandas as pd

MEASUREMENTS = {
    "soil_ph": {"label": "Soil pH", "unit": "pH", "minimum": 0, "maximum": 14},
    "organic_matter_pct": {"label": "Organic matter", "unit": "%", "minimum": 0, "maximum": 100},
    "electrical_conductivity_ds_m": {"label": "Electrical conductivity", "unit": "dS/m", "minimum": 0, "maximum": None},
    "nitrogen_mg_kg": {"label": "Nitrogen", "unit": "mg/kg", "minimum": 0, "maximum": None},
    "phosphorus_mg_kg": {"label": "Available phosphorus", "unit": "mg/kg", "minimum": 0, "maximum": None},
    "potassium_mg_kg": {"label": "Available potassium", "unit": "mg/kg", "minimum": 0, "maximum": None},
}

OPTIONAL_FIELDS = {
    "sample_id": "Sample ID",
    "depth_cm": "Sampling depth (cm)",
    "sample_date": "Sample date",
    "location": "Sample location",
}


def normalize_soil_lab_data(frame: pd.DataFrame, mapping: dict) -> tuple[pd.DataFrame, dict]:
    """Return a clean, analysis-ready table and a validation summary.

    mapping maps normalized field names to original column names. A value of
    None or an empty string means that field was not mapped.
    """
    if frame is None or frame.empty:
        return pd.DataFrame(), {"errors": ["The uploaded worksheet is empty."], "warnings": [], "mapped_measurements": []}

    selected = {}
    for field in list(MEASUREMENTS) + list(OPTIONAL_FIELDS):
        source = mapping.get(field)
        if source and source in frame.columns:
            selected[field] = source

    mapped_measurements = [field for field in MEASUREMENTS if field in selected]
    if not mapped_measurements:
        return pd.DataFrame(), {
            "errors": ["Map at least one measurement column (pH, organic matter, EC, N, P or K)."],
            "warnings": [],
            "mapped_measurements": [],
        }

    output = pd.DataFrame(index=frame.index)
    for field, source in selected.items():
        if field in MEASUREMENTS:
            values = pd.to_numeric(frame[source], errors="coerce")
            spec = MEASUREMENTS[field]
            invalid = values.notna() & (values < spec["minimum"])
            if spec["maximum"] is not None:
                invalid |= values.notna() & (values > spec["maximum"])
            values = values.mask(invalid)
            output[field] = values
        elif field == "depth_cm":
            output[field] = pd.to_numeric(frame[source], errors="coerce")
        elif field == "sample_date":
            output[field] = pd.to_datetime(frame[source], errors="coerce").dt.strftime("%Y-%m-%d")
        else:
            output[field] = frame[source].astype("string").str.strip()

    output.insert(0, "source_row", range(2, len(output) + 2))
    measurement_columns = [field for field in mapped_measurements if field in output]
    output["valid_measurement_count"] = output[measurement_columns].notna().sum(axis=1)
    output = output.loc[output["valid_measurement_count"] > 0].reset_index(drop=True)

    warnings = []
    if len(output) < len(frame):
        warnings.append(f"{len(frame) - len(output)} row(s) had no valid mapped measurement and were excluded.")
    for field in mapped_measurements:
        if field not in output or output[field].notna().sum() == 0:
            warnings.append(f"No valid numeric values were found for {MEASUREMENTS[field]['label']}.")
    for field in mapped_measurements:
        if field in output:
            invalid_count = pd.to_numeric(frame[selected[field]], errors="coerce").notna().sum() - output[field].notna().sum()
            if invalid_count > 0:
                warnings.append(f"{invalid_count} out-of-range or invalid {MEASUREMENTS[field]['label']} value(s) were treated as missing.")

    summary = {
        "errors": [],
        "warnings": list(dict.fromkeys(warnings)),
        "mapped_measurements": mapped_measurements,
        "rows_uploaded": int(len(frame)),
        "rows_with_measurements": int(len(output)),
        "valid_values": {field: int(output[field].notna().sum()) for field in mapped_measurements if field in output},
    }
    return output, summary


def soil_lab_summary(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Summarize available laboratory measurements without filling missing values."""
    rows = []
    for field, spec in MEASUREMENTS.items():
        if field not in cleaned:
            continue
        values = cleaned[field].dropna()
        if values.empty:
            continue
        rows.append({
            "Indicator": spec["label"],
            "Unit": spec["unit"],
            "Samples": int(values.count()),
            "Minimum": round(float(values.min()), 3),
            "Median": round(float(values.median()), 3),
            "Maximum": round(float(values.max()), 3),
        })
    return pd.DataFrame(rows)



def soil_lab_group_summary(cleaned: pd.DataFrame, group_by: str) -> pd.DataFrame:
    """Summarize median and sample count by a supplied sample field."""
    if group_by not in cleaned.columns:
        return pd.DataFrame()
    measurement_columns = [field for field in MEASUREMENTS if field in cleaned.columns]
    if not measurement_columns:
        return pd.DataFrame()
    grouped = cleaned.groupby(group_by, dropna=False)[measurement_columns].agg(["count", "median"]).reset_index()
    grouped.columns = [
        group_by if column[0] == group_by else f"{MEASUREMENTS[column[0]]['label']} {column[1]}"
        for column in grouped.columns.to_flat_index()
    ]
    return grouped
