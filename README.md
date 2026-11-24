# AgriNova AI

**Global AI-Powered Agricultural Intelligence Platform**

AgriNova AI is a Streamlit application designed for worldwide use. Its default experience is global: no country is preselected, and users can search for cities, regions or countries worldwide to load location-specific weather and climate data.

## Features
- Worldwide location search using Open-Meteo Geocoding (no API key)
- Global default experience; Somalia is searchable but is not the default region
- Six dashboard themes: Emerald, Forest, Ocean, Sunrise, Dark and Lavender
- Open-Meteo weather forecasts
- NASA POWER historical climate lookup
- Crop planning and general agronomic guidance
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
Worldwide location search does not mean every agricultural dataset is complete for every country or location. Data coverage, spatial resolution, update frequency and license vary by source. Crop guidance is general and requires local agronomic validation. Crop health screening is symptom-based, not automated photo diagnosis. Soil interpretations are not laboratory results. Check source licenses and service terms before commercial reuse.

## Data sources
Open-Meteo and its Geocoding API, NASA POWER, FAOSTAT, SoilGrids, Copernicus, NASA Earthdata, PlantVillage, CGIAR, HDX and IPC. Check individual dataset/service terms and licenses before redistribution or commercial use.

## License
MIT. See `LICENSE`.
