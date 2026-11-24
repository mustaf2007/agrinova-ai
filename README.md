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
- Offline searchable agricultural knowledge using TF-IDF
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

## Sources
- https://open-meteo.com/
- https://power.larc.nasa.gov/
- https://www.fao.org/faostat/
- https://www.isric.org/explore/soilgrids
- https://dataspace.copernicus.eu/
- https://earthdata.nasa.gov/
- https://plantvillage.psu.edu/
- https://cgspace.cgiar.org/
- https://data.humdata.org/
- https://www.ipcinfo.org/

See individual source terms and dataset licenses before redistribution.

## License
MIT. See `LICENSE`.