# AgriNova AI

**AI-Powered Agricultural Intelligence Platform**

AgriNova AI is a Streamlit application combining accessible agricultural knowledge, symptom-based crop health screening, weather forecasts, historical climate context, crop planning, soil indicator interpretation and configurable dashboard themes.

## Features
- Dashboard with six themes: Emerald, Forest, Ocean, Sunrise, Dark and Lavender
- Open-Meteo weather forecasts (no API key)
- NASA POWER historical climate lookup (no API key)
- Crop planning and agronomic guidance
- Symptom-based crop health screening
- Soil indicator interpretation
- Searchable curated agricultural knowledge using TF-IDF (no external AI API)
- Data source and methodology catalog

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Connect this public repository to [Streamlit Community Cloud](https://share.streamlit.io/), select branch `main`, and main file `app.py`. No secrets are needed for the included features.

## Important limitations
This initial release does not automatically diagnose uploaded crop images. It provides symptom-based screening. Local crop recommendations require validation by qualified agronomists; soil interpretations are not laboratory results. Check source licenses and service terms before commercial reuse.

## Data sources
Open-Meteo, NASA POWER, FAOSTAT, SoilGrids, Copernicus, NASA Earthdata, PlantVillage, CGIAR, HDX and IPC. Check individual dataset/service terms and licenses before redistribution or commercial use.

## License
MIT. See `LICENSE`.
