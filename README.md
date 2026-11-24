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
- Indicator-level crop environment checks comparing recent historical mean temperature and reported soil pH with available ECOCROP ranges; no composite suitability score is presented and incompatible rainfall periods are not compared
- Spatial Evidence Explorer for mapping user-uploaded CSV / Excel point observations with latitude, longitude, optional temperature and soil pH columns, plus point-level ECOCROP range checks where available
- GeoJSON farm and field boundary upload for Polygon / MultiPolygon validation, interactive map display and validated GeoJSON export
- Combined boundary and observation-point map with independently toggleable layers when both datasets are uploaded
- Global crop-calendar evidence catalogue covering FAO Crop Calendar, AQUASTAT, GAEZ v5, FAO Hand-in-Hand and University of Minnesota GEMS, with the African World Bank/JRC-ASAP dataset retained as a regional source
- Generic crop-calendar CSV / Excel explorer with user-confirmed column mapping, country/crop filtering and selectable dekad, month or source-value time formats
- Links to FAO Crop Calendar, ECOCROP/GAEZ and AQUASTAT for source-backed agronomic research
- ECOCROP values are clearly labelled as expert-compiled species-level estimates, not cultivar-specific prescriptions or farm measurements
- Unsupported variety-specific rates, planting dates and yield estimates are withheld rather than invented
- Symptom-based crop health screening
- Soil Health workspace with global SoilGrids source exploration, user-entered laboratory measurement interpretation, and CSV / Excel soil-lab data import with user-confirmed column mapping and validation
- Live SoilGrids WCS GetCapabilities discovery for the official nitrogen service, listing advertised coverage identifiers
- Bounded SoilGrids nitrogen GeoTIFF download for a validated GeoJSON boundary bounding rectangle, with WGS84-to-ISRIC Homolosine transformation, extent limits and TIFF-response validation
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
Worldwide location search does not mean every agricultural dataset is complete for every country or location. Data coverage, spatial resolution, update frequency and license vary by source. Crop planning requires a selected farm location and variety/cultivar. Country-level centroids are not accepted as farm locations unless exact coordinates are supplied. Users can click a farm location on the map or enter coordinates manually. ECOCROP ecological thresholds are species-level expert estimates with known missing values and are not cultivar-specific management recommendations. Indicator-level environment checks are deliberately limited: the recent approximately 90-day mean temperature is contextual rather than a full-season suitability test, soil pH comparisons require a reported value and available absolute ECOCROP range, and annual rainfall requirements are not compared with short-window climate data. No overall suitability score is generated. The Spatial Evidence Explorer maps user-supplied point observations and displays user-uploaded GeoJSON Polygon / MultiPolygon boundaries after basic coordinate and ring-closure checks. Boundary validation does not repair complex topology, verify ownership or calculate area. When both files are supplied, observation points and boundaries can be inspected together as separate map layers. It does not automatically download or sample GAEZ or SoilGrids raster cells or produce a validated suitability map. Coordinate and pH validation is applied, and source metadata, depth, units and reference periods should be retained. Global crop-calendar evidence is not complete or uniform: FAO Crop Calendar reports more than 100 crops in more than 50 countries; AQUASTAT irrigated calendars are historical and availability varies; GAEZ v5 provides global modeled agroecological, climate, crop-suitability and productivity layers, while FAO Hand-in-Hand provides a wider geospatial data portal; and the GEMS global calendar uses a circa-2007 reference period for selected crops. The generic CSV / Excel explorer requires users to upload source files and confirm field mappings. Country, crop and optional administrative-area text matching may not resolve every naming convention. The World Bank / JRC-ASAP dataset remains Africa-only, covers selected crops and 2019 dekad periods, and is not a current-season forecast. Dekad labels are approximate ten-day periods, not exact dates. FAO Crop Calendar and other location-specific planting, fertilizer, irrigation and yield recommendations are not yet programmatically matched; unavailable values are not guessed. Crop health screening is symptom-based, not automated photo diagnosis. Soil interpretations are not laboratory results. SoilGrids provides modeled global soil predictions at 250 m and six depth intervals, with uncertainty information; its REST point-query API is currently temporarily paused by ISRIC, so AgriNova AI does not display fabricated point estimates. Users can explore the official SoilGrids map and WMS/WCS alternatives. AgriNova's initial WCS integration checks live GetCapabilities metadata for the nitrogen service and can request a bounded GeoTIFF for a validated GeoJSON boundary bounding rectangle. The request uses ISRIC's documented Interrupted Goode Homolosine projection definition (pseudo-code EPSG:152160), is limited to 0.25 degrees in each direction and 20 MiB, and the response must pass a TIFF signature check. This is a bounding-rectangle download, not an exact polygon clip. The application does not yet interpret raster pixels or calculate farm-level zonal statistics. A successful metadata response confirms advertised coverages, not that every raster request or geographic subset will succeed. Missing soil measurements are left unclassified rather than silently filled with example defaults. The soil laboratory importer supports CSV and Excel files, explicit column mapping, range validation for pH and organic matter, descriptive summaries, grouped comparisons by sample location/depth/date, measurement distribution charts and validated CSV export; it does not infer fertilizer rates or regional soil classifications. Check source licenses and service terms before commercial reuse.

## Data sources
Open-Meteo and its Geocoding API, NASA POWER, FAOSTAT, ISRIC SoilGrids (official map and WMS/WCS access; REST point-query currently paused; WCS capabilities discovery and bounded nitrogen GeoTIFF subset download), Copernicus, NASA Earthdata, PlantVillage, CGIAR, HDX and IPC. Check individual dataset/service terms and licenses before redistribution or commercial use.

## License
MIT. See `LICENSE`.
