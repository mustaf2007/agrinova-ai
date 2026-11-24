from __future__ import annotations
import requests
import io
import pandas as pd
import streamlit as st
from datetime import date, timedelta

TIMEOUT = 20
DATA_SOURCES = [
    {"Category":"Crop calendars and agronomic practices","Provider":"FAO Crop Calendar","Coverage":"100+ crops in 50+ countries; agroecological-zone detail where available","Access":"Public searchable platform; coverage varies by country and crop","URL":"https://cropcalendar.apps.fao.org/"},
    {"Category":"Crop ecological requirements","Provider":"FAO ECOCROP / GAEZ","Coverage":"Ecological characteristics for approximately 2,568 plant species","Access":"Public database through GAEZ; records vary in detail","URL":"https://gaez.fao.org/pages/ecocrop"},
    {"Category":"Crop ecological requirements dataset","Provider":"FAO ECOCROP via CGIAR Climate Action Data Hub","Coverage":"2,568 species; ecological thresholds and crop-cycle descriptors; species-level, not cultivar-specific","Access":"Public CC BY 4.0 dataset; expert estimates with known gaps and limitations","URL":"https://cgiar-climate-data-hub.github.io/catalog/ecocrop/"},
    {"Category":"Irrigated crop calendars","Provider":"FAO AQUASTAT","Coverage":"Country-level irrigated crop calendar records for selected crops and years","Access":"Public database; coverage and reference years vary","URL":"https://www.fao.org/aquastat/en/databases/crop-calendar/"},
    {"Category":"Weather forecasts","Provider":"Open-Meteo","Coverage":"Global; location-level forecasts","Access":"Free access; no API key for eligible non-commercial use; check terms","URL":"https://open-meteo.com/"},
    {"Category":"Historical climate","Provider":"NASA POWER","Coverage":"Global gridded / point data","Access":"Public access; check dataset terms","URL":"https://power.larc.nasa.gov/"},
    {"Category":"Agriculture statistics","Provider":"FAOSTAT","Coverage":"Country and global statistics; varies by indicator","Access":"Public data; check individual dataset terms","URL":"https://www.fao.org/faostat/"},
    {"Category":"Soil properties","Provider":"ISRIC SoilGrids","Coverage":"Global modeled soil properties","Access":"Open data; check product license and service terms","URL":"https://www.isric.org/explore/soilgrids"},
    {"Category":"Satellite earth observation","Provider":"Copernicus Data Space","Coverage":"Global satellite observations","Access":"Free access to many products; account / quotas may apply for some services","URL":"https://dataspace.copernicus.eu/"},
    {"Category":"Satellite earth observation","Provider":"NASA Earthdata","Coverage":"Global earth observation products","Access":"Many datasets are free; some services require free registration","URL":"https://earthdata.nasa.gov/"},
    {"Category":"Crop disease images","Provider":"PlantVillage","Coverage":"Selected crops and controlled image conditions","Access":"Dataset access subject to its terms and license","URL":"https://plantvillage.psu.edu/"},
    {"Category":"Agricultural research","Provider":"CGIAR repositories","Coverage":"Global / regional research publications","Access":"Publicly accessible resources; check item-level rights","URL":"https://cgspace.cgiar.org/"},
    {"Category":"Humanitarian and administrative data","Provider":"Humanitarian Data Exchange","Coverage":"Country-specific datasets; Somalia included for many themes","Access":"Dataset-specific licenses and attribution apply","URL":"https://data.humdata.org/"},
    {"Category":"Food security","Provider":"IPC","Coverage":"Selected countries and periods","Access":"Public reports and analysis; check reuse terms","URL":"https://www.ipcinfo.org/"},
]

@st.cache_data(ttl=1800, show_spinner=False)
def get_weather(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude, "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 7, "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})
        daily = payload.get("daily", {})
        days = daily.get("time", [])
        rows = []
        for i, day in enumerate(days):
            rows.append({
                "date": day,
                "temp_max": daily.get("temperature_2m_max", [None] * len(days))[i],
                "temp_min": daily.get("temperature_2m_min", [None] * len(days))[i],
                "precipitation": daily.get("precipitation_sum", [None] * len(days))[i],
            })
        return {
            "current_temp": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind": current.get("wind_speed_10m"),
            "rain_7d": round(sum(row["precipitation"] or 0 for row in rows), 1),
            "daily": rows,
        }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def get_historical_climate(latitude: float, longitude: float):
    end = date.today() - timedelta(days=5)
    start = end - timedelta(days=89)
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON"
    }
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        properties = response.json().get("properties", {}).get("parameter", {})
        if not properties:
            return None
        temperature = properties.get("T2M", {})
        precipitation = properties.get("PRECTOTCORR", {})
        rows = []
        for key, value in temperature.items():
            rain = precipitation.get(key)
            if value is not None and value > -900 and rain is not None and rain > -900:
                rows.append({"date": pd.to_datetime(key, format="%Y%m%d"), "T2M": value, "PRECTOTCORR": rain})
        return pd.DataFrame(rows) if rows else None
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def search_global_locations(query: str, count: int = 10):
    """Search cities, regions and countries worldwide using Open-Meteo Geocoding."""
    query = (query or "").strip()
    if len(query) < 2:
        return []
    url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        response = requests.get(url, params={"name": query, "count": count, "language": "en", "format": "json"}, timeout=TIMEOUT)
        response.raise_for_status()
        results = response.json().get("results", [])
        locations = []
        for item in results:
            if item.get("latitude") is None or item.get("longitude") is None:
                continue
            parts = [item.get("name"), item.get("admin1"), item.get("country")]
            label = ", ".join(dict.fromkeys(str(part) for part in parts if part))
            locations.append({
                "label": label,
                "name": item.get("name", "Unknown"),
                "country": item.get("country", ""),
                "country_code": item.get("country_code", ""),
                "admin1": item.get("admin1", ""),
                "admin2": item.get("admin2", ""),
                "feature_code": item.get("feature_code", ""),
                "population": item.get("population"),
                "latitude": float(item["latitude"]),
                "longitude": float(item["longitude"]),
            })
        return locations
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []


ECOCROP_PARQUET_URL = "https://digital-atlas.s3.amazonaws.com/cdh/data/ecocrop/ecocrop.parquet"
ECOCROP_FIELDS = [
    "ecoportcode", "scientificname", "comname", "syno", "lifo", "lispa",
    "topmn", "topmx", "tmin", "tmax", "ktmp",
    "ropmn", "ropmx", "rmin", "rmax", "gmin", "gmax",
    "phopmn", "phopmx", "phmin", "phmax", "text", "textr", "cliz"
]

@st.cache_data(ttl=86400, show_spinner=False)
def load_ecocrop_database():
    """Load the public FAO ECOCROP species table distributed by CGIAR."""
    try:
        response = requests.get(ECOCROP_PARQUET_URL, timeout=TIMEOUT)
        response.raise_for_status()
        frame = pd.read_parquet(io.BytesIO(response.content), columns=ECOCROP_FIELDS)
        return frame
    except (requests.RequestException, ValueError, ImportError, OSError, KeyError):
        return None

def _ecocrop_text(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(part) for part in value if part is not None)
    return str(value)

@st.cache_data(ttl=86400, show_spinner=False)
def search_ecocrop(crop_name: str, limit: int = 12):
    """Find species-level ECOCROP records by scientific, common or synonym name."""
    query = (crop_name or "").strip().casefold()
    if len(query) < 2:
        return []
    frame = load_ecocrop_database()
    if frame is None or frame.empty:
        return []
    matches = []
    for _, row in frame.iterrows():
        scientific = _ecocrop_text(row.get("scientificname"))
        common = _ecocrop_text(row.get("comname"))
        synonyms = _ecocrop_text(row.get("syno"))
        terms = [scientific.casefold()] + [part.strip().casefold() for part in common.split(",")] + [part.strip().casefold() for part in synonyms.split(",")]
        if query in terms:
            score = 0
        elif any(query in term for term in terms if term):
            score = 1
        else:
            continue
        record = {field: row.get(field) for field in ECOCROP_FIELDS if field in frame.columns}
        record["_match_score"] = score
        record["_display"] = f"{scientific} — {common or 'common name not listed'}"
        matches.append(record)
    matches.sort(key=lambda item: (item["_match_score"], str(item.get("scientificname", ""))))
    return matches[:limit]
