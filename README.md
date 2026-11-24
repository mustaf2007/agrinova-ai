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
- Recent approximately 90-day NASA POWER historical temperature and precipitation context in the crop planning profile, with valid-day coverage shown (daily product typically ends five days before the current date)
- Downloadable Global Farm Intelligence Report in PDF and CSV formats; CSV includes daily seven-day forecast and available historical climate observations alongside farm details and ECOCROP evidence
- Interactive farm map pin selection and optional manual farm coordinates
- FAO ECOCROP species-level ecological reference lookup (temperature, rainfall, soil pH, soil texture and crop-cycle fields where available)
- Global crop-calendar evidence catalogue covering FAO Crop Calendar, AQUASTAT, GAEZ v5, FAO Hand-in-Hand and University of Minnesota GEMS, with the African World Bank/JRC-ASAP dataset retained as a regional source
- Generic crop-calendar CSV / Excel explorer with user-confirmed column mapping, country/crop filtering and selectable dekad, month or source-value time formats
- Links to FAO Crop Calendar, ECOCROP/GAEZ and AQUASTAT for source-backed agronomic research
- ECOCROP values are clearly labelled as expert-compiled species-level estimates, not cultivar-specific prescriptions or farm measurements
- Unsupported variety-specific rates, planting dates and yield estimates are withheld rather than invented
- Symptom-based crop health screening
- Soil Health workspace with global SoilGrids source exploration and optional interpretation of user-entered laboratory measurements
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
Worldwide location search does not mean every agricultural dataset is complete for every country or location. Data coverage, spatial resolution, update frequency and license vary by source. Crop planning requires a selected farm location and variety/cultivar. Country-level centroids are not accepted as farm locations unless exact coordinates are supplied. Users can click a farm location on the map or enter coordinates manually. ECOCROP ecological thresholds are species-level expert estimates with known missing values and are not cultivar-specific management recommendations. Global crop-calendar evidence is not complete or uniform: FAO Crop Calendar reports more than 100 crops in more than 50 countries; AQUASTAT irrigated calendars are historical and availability varies; GAEZ v5 provides global modeled agroecological, climate, crop-suitability and productivity layers, while FAO Hand-in-Hand provides a wider geospatial data portal; and the GEMS global calendar uses a circa-2007 reference period for selected crops. The generic CSV / Excel explorer requires users to upload source files and confirm field mappings. Country, crop and optional administrative-area text matching may not resolve every naming convention. The World Bank / JRC-ASAP dataset remains Africa-only, covers selected crops and 2019 dekad periods, and is not a current-season forecast. Dekad labels are approximate ten-day periods, not exact dates. FAO Crop Calendar and other location-specific planting, fertilizer, irrigation and yield recommendations are not yet programmatically matched; unavailable values are not guessed. Crop health screening is symptom-based, not automated photo diagnosis. Soil interpretations are not laboratory results. SoilGrids provides modeled global soil predictions at 250 m and six depth intervals, with uncertainty information; its REST point-query API is currently temporarily paused by ISRIC, so AgriNova AI does not display fabricated point estimates. Users can explore the official SoilGrids map and WMS/WCS alternatives. Missing soil measurements are left unclassified rather than silently filled with example defaults. Check source licenses and service terms before commercial reuse.

## Data sources
Open-Meteo and its Geocoding API, NASA POWER, FAOSTAT, ISRIC SoilGrids (official map and WMS/WCS access; REST point-query currently paused), Copernicus, NASA Earthdata, PlantVillage, CGIAR, HDX and IPC. Check individual dataset/service terms and licenses before redistribution or commercial use.

## License
MIT. See `LICENSE`.
