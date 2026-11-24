"""Controlled SoilGrids WCS access for small nitrogen raster subsets.

Only user-supplied farm boundary extents are accepted. This module downloads a
GeoTIFF subset and validates its file signature; it does not interpret raster
pixels or calculate farm statistics.
"""
from __future__ import annotations

import math
import requests
from pyproj import CRS, Transformer

SOILGRIDS_NITROGEN_WCS = "https://maps.isric.org/mapserv?map=/map/nitrogen.map"
SOILGRIDS_WCS_DOCS = "https://docs.isric.org/globaldata/soilgrids/wcs.html"
SOILGRIDS_SUBSETTING_CRS = "http://www.opengis.net/def/crs/EPSG/0/152160"
SOILGRIDS_OUTPUT_CRS = SOILGRIDS_SUBSETTING_CRS
SOILGRIDS_HOMOLOSINE_PROJ4 = "+proj=igh +datum=WGS84 +no_defs +towgs84=0,0,0"
MAX_BOUNDING_BOX_DEGREES = 0.25
MAX_GEOTIFF_BYTES = 20 * 1024 * 1024


def parse_wcs_coverages(xml_text: str) -> list[str]:
    """Extract advertised coverage identifiers from a WCS capabilities XML."""
    import xml.etree.ElementTree as ET

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
        params={"SERVICE": "WCS", "VERSION": "2.0.0", "REQUEST": "GetCapabilities"},
        timeout=timeout,
        headers={"User-Agent": "AgriNova-AI/1.0 (SoilGrids WCS metadata discovery)"},
    )
    response.raise_for_status()
    return parse_wcs_coverages(response.text)


def get_coverage_request_params(coverage_id: str, bounds_wgs84: list[list[float]]) -> list[tuple[str, str]]:
    """Build a bounded WCS GetCoverage request using the documented SoilGrids CRS."""
    if not isinstance(coverage_id, str) or not coverage_id.startswith("nitrogen_"):
        raise ValueError("Only advertised nitrogen coverage identifiers are supported.")
    if not isinstance(bounds_wgs84, list) or len(bounds_wgs84) != 2:
        raise ValueError("Bounds must contain southwest and northeast coordinate pairs.")
    try:
        south, west = map(float, bounds_wgs84[0])
        north, east = map(float, bounds_wgs84[1])
    except (TypeError, ValueError):
        raise ValueError("Bounds must contain numeric latitude and longitude values.")
    if not all(math.isfinite(v) for v in (south, west, north, east)):
        raise ValueError("Bounds must be finite numbers.")
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("Geographic bounds are invalid.")
    if north - south > MAX_BOUNDING_BOX_DEGREES or east - west > MAX_BOUNDING_BOX_DEGREES:
        raise ValueError(
            f"Farm boundary extent is too large for this interactive request. "
            f"Maximum width and height are {MAX_BOUNDING_BOX_DEGREES} degrees."
        )

    transformer = Transformer.from_crs(
        "EPSG:4326",
        CRS.from_proj4(SOILGRIDS_HOMOLOSINE_PROJ4),
        always_xy=True,
    )
    corners = [
        transformer.transform(west, south),
        transformer.transform(west, north),
        transformer.transform(east, south),
        transformer.transform(east, north),
    ]
    xs = [point[0] for point in corners]
    ys = [point[1] for point in corners]
    if not all(math.isfinite(v) for v in xs + ys):
        raise ValueError("Could not transform farm boundary coordinates to the SoilGrids CRS.")
    return [
        ("SERVICE", "WCS"),
        ("VERSION", "2.0.1"),
        ("REQUEST", "GetCoverage"),
        ("COVERAGEID", coverage_id),
        ("FORMAT", "GEOTIFF_INT16"),
        ("SUBSET", f"X({min(xs):.2f},{max(xs):.2f})"),
        ("SUBSET", f"Y({min(ys):.2f},{max(ys):.2f})"),
        ("SUBSETTINGCRS", SOILGRIDS_SUBSETTING_CRS),
        ("OUTPUTCRS", SOILGRIDS_OUTPUT_CRS),
    ]


def fetch_nitrogen_geotiff(
    coverage_id: str,
    bounds_wgs84: list[list[float]],
    timeout: int = 45,
) -> bytes:
    """Download a small SoilGrids GeoTIFF subset for a validated farm extent."""
    params = get_coverage_request_params(coverage_id, bounds_wgs84)
    response = requests.get(
        SOILGRIDS_NITROGEN_WCS,
        params=params,
        timeout=timeout,
        headers={"User-Agent": "AgriNova-AI/1.0 (bounded SoilGrids WCS coverage request)"},
        stream=True,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    chunks, total = [], 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_GEOTIFF_BYTES:
            raise ValueError("The requested raster exceeds the 20 MiB interactive download limit.")
        chunks.append(chunk)
    payload = b"".join(chunks)
    is_tiff = payload.startswith(b"II*\x00") or payload.startswith(b"MM\x00*")
    if not is_tiff or ("xml" in content_type and "tiff" not in content_type):
        raise ValueError("The WCS response was not a valid GeoTIFF. The service may have returned an OGC exception.")
    return payload



def analyze_nitrogen_geotiff(
    raster_bytes: bytes,
    boundary_geojson: dict,
    all_touched: bool = False,
) -> dict:
    """Clip a SoilGrids nitrogen raster to GeoJSON polygons and summarize valid pixels.

    Returns descriptive statistics in the source layer's cg/kg units, coverage
    counts, raster metadata, and an exact-polygon-clipped GeoTIFF. This is a
    summary of modeled SoilGrids pixels, not a laboratory measurement.
    """
    import numpy as np
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import transform_geom

    if not isinstance(raster_bytes, (bytes, bytearray)) or not raster_bytes:
        raise ValueError("A non-empty GeoTIFF byte stream is required.")
    if not isinstance(boundary_geojson, dict):
        raise ValueError("A validated GeoJSON boundary is required.")
    if boundary_geojson.get("type") == "FeatureCollection":
        features = boundary_geojson.get("features", [])
    elif boundary_geojson.get("type") == "Feature":
        features = [boundary_geojson]
    else:
        raise ValueError("Boundary must be a GeoJSON Feature or FeatureCollection.")

    geometries = []
    for feature in features:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            continue
        geometries.append(geometry)
    if not geometries:
        raise ValueError("No Polygon or MultiPolygon geometries were found.")

    try:
        with rasterio.io.MemoryFile(bytes(raster_bytes)) as memory_file:
            with memory_file.open() as dataset:
                if dataset.count < 1 or dataset.crs is None:
                    raise ValueError("The GeoTIFF must contain at least one band and a defined CRS.")
                if dataset.width * dataset.height > 25_000_000:
                    raise ValueError("Raster dimensions exceed the interactive processing limit.")
                transformed = [
                    transform_geom("EPSG:4326", dataset.crs, geometry, precision=-1)
                    for geometry in geometries
                ]
                clipped, transform = mask(
                    dataset,
                    transformed,
                    all_touched=all_touched,
                    crop=True,
                    filled=False,
                    indexes=1,
                )
                raw = np.asarray(clipped.data)
                masked = np.ma.getmaskarray(clipped) | ~np.isfinite(raw)
                values = raw[~masked].astype("float64")
                # Count polygon-selected pixels separately from valid raster cells.
                from rasterio.mask import raster_geometry_mask
                shape_mask, _, _ = raster_geometry_mask(
                    dataset, transformed, all_touched=all_touched, crop=True
                )
                inside_pixels = int(np.count_nonzero(~shape_mask))
                valid_pixels = int(values.size)
                if inside_pixels == 0:
                    raise ValueError("The uploaded polygon contains no raster pixel centres at this resolution.")
                if valid_pixels == 0:
                    raise ValueError("No valid SoilGrids pixels overlap the uploaded polygon.")
                nodata_pixels = inside_pixels - valid_pixels

                profile = dataset.profile.copy()
                profile.update(
                    driver="GTiff",
                    height=clipped.shape[0],
                    width=clipped.shape[1],
                    count=1,
                    transform=transform,
                    compress="deflate",
                    nodata=dataset.nodata if dataset.nodata is not None else -32768,
                )
                export_array = np.ma.array(clipped, mask=np.ma.getmaskarray(clipped) | shape_mask)
                with rasterio.io.MemoryFile() as output_memory:
                    with output_memory.open(**profile) as writer:
                        writer.write(export_array.filled(profile["nodata"]).astype(profile["dtype"]), 1)
                    clipped_bytes = output_memory.read()

                return {
                    "pixel_count_inside_polygon": inside_pixels,
                    "valid_pixel_count": valid_pixels,
                    "nodata_pixel_count": nodata_pixels,
                    "valid_coverage_pct": round(valid_pixels / inside_pixels * 100, 2),
                    "mean_cg_kg": float(np.mean(values)),
                    "median_cg_kg": float(np.median(values)),
                    "minimum_cg_kg": float(np.min(values)),
                    "maximum_cg_kg": float(np.max(values)),
                    "std_cg_kg": float(np.std(values, ddof=0)),
                    "q25_cg_kg": float(np.quantile(values, 0.25)),
                    "q75_cg_kg": float(np.quantile(values, 0.75)),
                    "raster_crs": str(dataset.crs),
                    "raster_resolution": tuple(float(abs(v)) for v in dataset.res),
                    "all_touched": bool(all_touched),
                    "clipped_geotiff": clipped_bytes,
                }
    except ValueError:
        raise
    except Exception as error:
        raise ValueError(f"Could not interpret or clip the SoilGrids GeoTIFF: {error}") from error
