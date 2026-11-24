# AgriNova AI

**Global AI-Powered Agricultural Intelligence Platform**

AgriNova AI is a Streamlit application designed for worldwide use. Its default experience is global: no country is preselected, and users can search for cities, regions or countries worldwide to load location-specific weather and climate data.

## Features
- Worldwide location search using Open-Meteo Geocoding (no API key)
- Global default experience; Somalia is searchable but is not the default region
- Six dashboard themes: Emerald, Forest, Ocean, Sunrise, Dark and Lavender
- Open-Meteo weather forecasts
- NASA POWER historical climate lookup
- Crop planning for any entered crop or plant, with required farm location and variety/cultivar
- Location-specific live weather context in the crop planning profile
- Interactive farm map pin selection and optional manual farm coordinates
- FAO ECOCROP species-level ecological reference lookup (temperature, rainfall, soil pH, soil texture and crop-cycle fields where available)
- Links to FAO Crop Calendar, ECOCROP/GAEZ and AQUASTAT for source-backed agronomic research
- ECOCROP values are clearly labelled as expert-compiled species-level estimates, not cultivar-specific prescriptions or farm measurements
- Unsupported variety-specific rates, planting dates and yield estimates are withheld rather than invented
- Symptom-based crop health screening
- User-entered soil indicator interpretation
- Searchable curated agricultural knowledge using TF-IDF (no external AI API)
- Data source and methodology catalog

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Connect this public repository to [Streamlit Community Cloud](https://share.streamlit.io/), select branch `main`, and main file `app.py`. No secrets are needed for the included location, weather and climate features.

## Important limitations
Worldwide location search does not mean every agricultural dataset is complete for every country or location. Data coverage, spatial resolution, update frequency and license vary by source. Crop planning requires a selected farm location and variety/cultivar. Country-level centroids are not accepted as farm locations unless exact coordinates are supplied. Users can click a farm location on the map or enter coordinates manually. ECOCROP ecological thresholds are species-level expert estimates with known missing values and are not cultivar-specific management recommendations. FAO Crop Calendar and other location-specific planting, fertilizer, irrigation and yield recommendations are not yet programmatically matched; unavailable values are not guessed. Crop health screening is symptom-based, not automated photo diagnosis. Soil interpretations are not laboratory results. Check source licenses and service terms before commercial reuse.

## Data sources
Open-Meteo and its Geocoding API, NASA POWER, FAOSTAT, SoilGrids, Copernicus, NASA Earthdata, PlantVillage, CGIAR, HDX and IPC. Check individual dataset/service terms and licenses before redistribution or commercial use.

## License
MIT. See `LICENSE`.
