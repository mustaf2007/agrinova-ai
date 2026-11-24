import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from modules.data_sources import get_weather, get_historical_climate, search_global_locations, search_ecocrop, DATA_SOURCES
from modules.agronomy import CROPS, get_crop_guidance, assess_soil, screen_crop_symptoms, search_knowledge, KNOWLEDGE
from modules.reporting import build_farm_report_csv, build_farm_report_pdf
from modules.soil_lab import MEASUREMENTS, OPTIONAL_FIELDS, normalize_soil_lab_data, soil_lab_summary, soil_lab_group_summary
from modules.crop_suitability import assess_crop_environment, normalize_spatial_observations

st.set_page_config(page_title='AgriNova AI | Agricultural Intelligence', page_icon='🌱', layout='wide')
THEMES = {
 'Emerald': {'bg':'#F4F8F3','panel':'#FFFFFF','text':'#18352A','muted':'#60766B','accent':'#16845B','soft':'#DDF2E7','border':'#DCE8DF'},
 'Forest': {'bg':'#EDF4EF','panel':'#F9FCF9','text':'#173B2A','muted':'#557565','accent':'#236B45','soft':'#D7EBDD','border':'#C8DDCF'},
 'Ocean': {'bg':'#F0F6FA','panel':'#FFFFFF','text':'#193449','muted':'#60798B','accent':'#1976A8','soft':'#DCEFFA','border':'#D4E4EE'},
 'Sunrise': {'bg':'#FBF5EF','panel':'#FFFFFF','text':'#49301F','muted':'#8A6C56','accent':'#C56A2D','soft':'#FBE8D9','border':'#EEDCCB'},
 'Dark': {'bg':'#111B18','panel':'#1B2924','text':'#E7F1EA','muted':'#A8BDB0','accent':'#53C58B','soft':'#243D32','border':'#30483C'},
 'Lavender': {'bg':'#F6F4FA','panel':'#FFFFFF','text':'#342D49','muted':'#766D8C','accent':'#7861B5','soft':'#EAE4F7','border':'#E2DCEF'},
}
if 'theme' not in st.session_state: st.session_state.theme = 'Emerald'
if 'cases' not in st.session_state: st.session_state.cases = []
t = THEMES[st.session_state.theme]
st.markdown(f'''<style>.stApp{{background:{t['bg']};color:{t['text']}}}[data-testid="stSidebar"]{{background:{t['panel']};border-right:1px solid {t['border']}}}[data-testid="stSidebar"] *{{color:{t['text']}}}.block-container{{max-width:1500px;padding-top:1.4rem}}h1,h2,h3,p,label{{color:{t['text']}}}.hero{{background:linear-gradient(120deg,{t['soft']},{t['panel']});border:1px solid {t['border']};padding:1.4rem;border-radius:18px;margin-bottom:1rem}}.metric-card{{background:{t['panel']};border:1px solid {t['border']};border-radius:14px;padding:1rem;min-height:105px}}.metric-label{{color:{t['muted']};font-size:.82rem}}.metric-value{{color:{t['text']};font-size:1.5rem;font-weight:700}}.stButton>button{{background:{t['accent']};color:white;border:0;border-radius:9px}}hr{{border-color:{t['border']}}}footer{{visibility:hidden}}</style>''',unsafe_allow_html=True)
def metric(label,value,note=''):
 st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-label">{note}</div></div>',unsafe_allow_html=True)

def crop_plant_picker(key, label="Crop or plant"):
 options = list(CROPS) + ["Other / any crop or plant"]
 selected = st.selectbox(label, options, key=f"{key}_crop_choice")
 if selected == "Other / any crop or plant":
  custom = st.text_input("Enter crop or plant name", placeholder="e.g. cassava, avocado, coffee, mango, wheat, herbs, pasture grass", key=f"{key}_custom_crop")
  return custom.strip() or "Custom crop / plant"
 return selected

def _country_flag(country_code):
 code = (country_code or "").upper()
 if len(code) != 2 or not code.isalpha():
  return "🌍"
 return "".join(chr(127397 + ord(char)) for char in code)

def _location_type(feature_code):
 code = (feature_code or "").upper()
 if code == "PCLI" or code.startswith("PCL"):
  return "Country"
 if code.startswith("ADM1"):
  return "State / province"
 if code.startswith("ADM2"):
  return "District / county"
 if code.startswith("ADM"):
  return "Administrative area"
 if code.startswith("PPL"):
  return "City / town / settlement"
 return "Place"

def _is_country_location(location):
 return (location or {}).get("feature_code", "").upper() in {"PCLI", "PCL"}

def global_location_picker(key, label="Search location worldwide"):
 query = st.text_input(label, placeholder="Enter a city, region or country (e.g. Nairobi, Punjab, Brazil)", key=f"{key}_global_search")
 if len(query.strip()) < 2:
  st.caption("Worldwide search is available. Enter at least two characters to find and select a location.")
  return None
 matches = search_global_locations(query)
 if not matches:
  st.info("No matching locations found. Try a nearby city, a different spelling or a country name.")
  return None
 st.caption(f"{len(matches)} matching location(s) found. Select the exact place to use its coordinates for local data.")
 options = {}
 for index, item in enumerate(matches):
  flag = _country_flag(item.get("country_code"))
  kind = _location_type(item.get("feature_code"))
  display = f"{flag}  {item['label']}  ·  {kind}"
  if display in options:
   display = f"{display}  ({item['latitude']:.3f}, {item['longitude']:.3f})"
  options[display] = item
 selected_label = st.selectbox("Matching locations", list(options), key=f"{key}_global_match")
 selected = options[selected_label]
 st.success(f"Selected location: {selected['label']}")
 with st.expander("Location details"):
  d1, d2, d3 = st.columns(3)
  with d1:
   st.write(f"**Type**  \n{_location_type(selected.get('feature_code'))}")
  with d2:
   st.write(f"**Country**  \n{selected.get('country') or 'Not available'}")
  with d3:
   population = selected.get("population")
   st.write(f"**Population**  \n{f'{population:,}' if isinstance(population, (int, float)) else 'Not available'}")
  st.caption(f"Coordinates: {selected['latitude']:.5f}°, {selected['longitude']:.5f}°")
 if _is_country_location(selected):
  st.warning("Country-level reference point: these coordinates are not a farm location and may not represent national weather conditions. Select a city, district or region for more localized results.")
 else:
  st.caption("This is a subnational location match. It is more localized than a country reference point, but may still differ from conditions at the exact farm.")
 return selected
with st.sidebar:
 st.markdown('## 🌱 AgriNova AI'); st.caption('Agricultural Intelligence Platform'); st.divider()
 page=st.radio('WORKSPACE',['Overview','Crop Health Screening','Weather & Climate','Crop Planner','Spatial Evidence Explorer','Soil Health','Agri Knowledge Assistant','Data Sources & Methodology'])
 st.divider(); theme=st.selectbox('Appearance theme',list(THEMES),index=list(THEMES).index(st.session_state.theme))
 if theme!=st.session_state.theme: st.session_state.theme=theme; st.rerun()
 st.caption('Free-data-first • No paid API keys')
if page=='Overview':
 st.markdown('<div class="hero"><h1>🌱 AgriNova AI</h1><p>AI-powered agricultural intelligence for healthier crops and better farming decisions.</p></div>',unsafe_allow_html=True)
 location = global_location_picker("overview")
 crop=crop_plant_picker('overview', 'Crop or plant focus')
 w = get_weather(location["latitude"], location["longitude"]) if location else None
 x1,x2,x3,x4=st.columns(4)
 with x1: metric('Geographic coverage','Worldwide','Search any country, region or city')
 with x2: metric('Crop focus',crop,'Planning selection')
 with x3: metric('Temperature',f"{w['current_temp']} °C" if w and w.get('current_temp') is not None else 'Select location','Open-Meteo forecast')
 with x4: metric('7-day rainfall',f"{w['rain_7d']} mm" if w else 'Select location','Forecast total')
 st.subheader('Weather outlook')
 if w and w['daily']:
  if _is_country_location(location):
   st.warning("These forecast values use a country-level reference coordinate. Do not interpret them as representative of the entire country.")
  df=pd.DataFrame(w['daily']); st.plotly_chart(px.bar(df,x='date',y='precipitation',labels={'date':'Date','precipitation':'Rainfall (mm)'}),use_container_width=True)
 elif not location:
  st.info('AgriNova AI is in worldwide mode. Search for any location above to view its local weather and climate indicators.')
 else: st.info('Live forecast unavailable. Other modules remain usable.')
 st.info('Use the navigation to explore crop health screening, planning, soil indicators and agricultural knowledge.')
elif page=='Crop Health Screening':
 st.markdown('<div class="hero"><h1>🩺 Crop Health Screening</h1><p>Screen observed symptoms and receive cautious next steps.</p></div>',unsafe_allow_html=True)
 st.warning('This is symptom-based screening, not automated photo diagnosis. Confirm findings with an agricultural specialist before treatment.')
 location = global_location_picker("health", "Search farm location worldwide (optional)")
 with st.form('health'):
  a,b=st.columns(2)
  with a: crop=crop_plant_picker('health', 'Crop or plant'); part=st.selectbox('Affected part',['Leaves','Stem','Roots','Fruit / grain','Whole plant']); symptoms=st.multiselect('Symptoms',['Yellowing leaves','Brown or black spots','White powdery growth','Wilting','Holes or chewing damage','Mosaic / mottled pattern','Stunted growth','Rotting / soft tissue','Rust-colored pustules','Leaf edges drying'])
  with b: severity=st.select_slider('Severity',['Low','Moderate','High','Severe'],value='Moderate'); conditions=st.multiselect('Recent conditions',['Heavy rainfall','High humidity','Hot and dry weather','Waterlogging','Recent irrigation','Unknown'])
  photo=st.file_uploader('Optional crop photograph (JPG/PNG)',type=['jpg','jpeg','png']); submit=st.form_submit_button('Screen symptoms',use_container_width=True)
 if submit:
  location_name = location["label"] if location else "Not specified"
  r=screen_crop_symptoms(crop,symptoms,part,conditions); st.session_state.cases.append({'crop':crop,'location':location_name,'severity':severity,'screening':r['likely_issue']})
  st.subheader('Screening result'); st.markdown(f"**Possible issue:** {r['likely_issue']}"); st.write(r['explanation'])
  for item in r['actions']: st.markdown('- '+item)
  if photo: st.image(photo,width=400,caption='Uploaded reference image; not automatically classified')
  st.warning('Preliminary screening only. Several disorders have similar symptoms. Seek local confirmation before using pesticides.')
 if st.session_state.cases: st.subheader('Recent screening records'); st.dataframe(pd.DataFrame(st.session_state.cases),use_container_width=True)
elif page=='Weather & Climate':
 st.markdown('<div class="hero"><h1>🌦️ Weather & Climate</h1><p>Forecast and historical climate indicators from free data services.</p></div>',unsafe_allow_html=True)
 loc = global_location_picker("weather")
 w = get_weather(loc["latitude"], loc["longitude"]) if loc else None
 if st.button('Refresh data'): st.cache_data.clear(); st.rerun()
 if w:
  if _is_country_location(loc):
   st.warning("Country-level reference coordinates are being used. For locally meaningful weather and climate analysis, select a city, district or region.")
  a,b,c,d=st.columns(4)
  with a: metric('Temperature',f"{w['current_temp']} °C")
  with b: metric('Humidity',f"{w['humidity']}%")
  with c: metric('Wind',f"{w['wind']} km/h")
  with d: metric('7-day rain',f"{w['rain_7d']} mm")
  df=pd.DataFrame(w['daily']); st.plotly_chart(px.line(df,x='date',y=['temp_max','temp_min'],markers=True),use_container_width=True); st.plotly_chart(px.bar(df,x='date',y='precipitation'),use_container_width=True)
  st.subheader('NASA POWER historical climate'); hist=get_historical_climate(loc["latitude"],loc["longitude"])
  if hist is not None and not hist.empty: st.line_chart(hist.set_index('date')[['T2M','PRECTOTCORR']]); st.dataframe(hist.tail(30),use_container_width=True)
  else: st.info('Historical data not currently returned by NASA POWER.')
 else: st.info('Worldwide mode is active. Search a city, region or country above to load its forecast. If you already selected a location, check internet connectivity.')
elif page=='Crop Planner':
 st.markdown('<div class="hero"><h1>🌾 Crop Planning</h1><p>Build a crop-specific planning record using the actual farm location and cultivar.</p></div>',unsafe_allow_html=True)
 st.info('Farm location and crop variety are required. Recommendations must be supported by crop- and location-specific evidence; unsupported values are not guessed.')
 region = global_location_picker("planner", "Search and select the farm location (required)")
 map_point = st.session_state.get("planner_map_point")
 if region:
  if st.session_state.get("planner_map_location") != region["label"]:
   st.session_state.pop("planner_map_point", None)
   st.session_state["planner_map_location"] = region["label"]
   map_point = None
  st.subheader("Pin the farm on the map")
  st.caption("Click the farm's position on the map. The pin coordinates can be used for more localized weather data.")
  map_center = [map_point["latitude"], map_point["longitude"]] if map_point else [region["latitude"], region["longitude"]]
  farm_map = folium.Map(location=map_center, zoom_start=13 if map_point else 7, control_scale=True)
  folium.Marker([region["latitude"], region["longitude"]], tooltip="Selected search location", icon=folium.Icon(color="blue", icon="info-sign")).add_to(farm_map)
  if map_point:
   folium.Marker([map_point["latitude"], map_point["longitude"]], tooltip="Selected farm point", icon=folium.Icon(color="green", icon="leaf")).add_to(farm_map)
  map_result = st_folium(farm_map, height=380, width=None, key="planner_farm_map", returned_objects=["last_clicked"])
  if map_result and map_result.get("last_clicked"):
   clicked = map_result["last_clicked"]
   new_point = {"latitude": float(clicked["lat"]), "longitude": float(clicked["lng"])}
   if new_point != map_point:
    st.session_state["planner_map_point"] = new_point
    st.session_state["planner_map_location"] = region["label"]
    st.rerun()
  if map_point:
   st.success(f"Farm pin selected: {map_point['latitude']:.5f}°, {map_point['longitude']:.5f}°")
   if st.button("Clear farm map pin", key="clear_planner_map_pin"):
    st.session_state.pop("planner_map_point", None)
    st.rerun()
 with st.form('crop_planner'):
  a,b=st.columns(2)
  with a:
   crop=crop_plant_picker('planner', 'Crop or plant (required)')
   variety=st.text_input('Crop variety / cultivar (required)',placeholder='Enter the exact variety name, or type “Unknown” only if not identified')
   area=st.number_input('Farm size (hectares)',min_value=.01,value=1.0,step=.5)
  with b:
   season=st.selectbox('Production season',['Main rainy season','Short rainy season','Dry / irrigated season','Year-round / perennial','Not sure'])
   system=st.selectbox('Production system',['Rainfed','Irrigated','Rainfed and supplementary irrigation','Protected cultivation','Not sure'])
   soil_ph=st.number_input('Soil pH (optional; enter 0 if not tested)',min_value=0.0,max_value=14.0,value=0.0,step=.1)
  st.markdown('**Optional: use exact farm coordinates**')
  use_farm_coordinates=st.checkbox('Use exact farm coordinates',value=bool(map_point))
  default_lat=float(map_point['latitude']) if map_point else (float(region['latitude']) if region else 0.0)
  default_lon=float(map_point['longitude']) if map_point else (float(region['longitude']) if region else 0.0)
  coord1,coord2=st.columns(2)
  with coord1:
   farm_lat=st.number_input('Farm latitude',min_value=-90.0,max_value=90.0,value=default_lat,step=0.0001,format='%.5f',disabled=not use_farm_coordinates)
  with coord2:
   farm_lon=st.number_input('Farm longitude',min_value=-180.0,max_value=180.0,value=default_lon,step=0.0001,format='%.5f',disabled=not use_farm_coordinates)
  st.caption('Map-selected coordinates are prefilled automatically. You can adjust them manually or enter coordinates from a GPS device.')
  submitted=st.form_submit_button('Build crop planning profile',use_container_width=True)
 if submitted:
  st.session_state.pop('farm_intelligence_report', None)
  if not region:
   st.error('Search for and select the country, region, district or nearest settlement for the farm.')
  elif _is_country_location(region) and not use_farm_coordinates:
   st.error('A country-level reference point is too broad for farm planning. Select a city, town, district or region, or provide exact farm coordinates.')
  elif not crop.strip() or crop == 'Custom crop / plant':
   st.error('Enter a specific crop or plant name.')
  elif not variety.strip():
   st.error('Enter the crop variety or cultivar. If it is genuinely unknown, enter “Unknown”; variety-specific recommendations will then be withheld.')
  else:
   planning_lat=float(farm_lat) if use_farm_coordinates else float(region['latitude'])
   planning_lon=float(farm_lon) if use_farm_coordinates else float(region['longitude'])
   weather=get_weather(planning_lat,planning_lon)
   st.subheader('Farm and crop profile')
   p1,p2,p3,p4=st.columns(4)
   with p1: metric('Crop / plant',crop)
   with p2: metric('Variety / cultivar',variety)
   with p3: metric('Farm location','Exact farm coordinates' if use_farm_coordinates else region['label'])
   with p4: metric('Farm size',f'{area:g} ha')
   if use_farm_coordinates:
    st.write(f'**Farm coordinates:** {planning_lat:.5f}°, {planning_lon:.5f}°')
   else:
    st.caption('Weather is based on the selected settlement or administrative-area reference point, not an exact farm GPS location.')
   st.write(f"**Production season:** {season}  |  **Production system:** {system}")
   if soil_ph > 0: st.write(f'**Reported soil pH:** {soil_ph:.1f}')
   if weather:
    st.subheader('Observed planning context')
    w1,w2,w3=st.columns(3)
    with w1: metric('Current temperature',f"{weather['current_temp']} °C" if weather.get('current_temp') is not None else 'Not returned')
    with w2: metric('Relative humidity',f"{weather['humidity']}%" if weather.get('humidity') is not None else 'Not returned')
    with w3: metric('Forecast rainfall (7 days)',f"{weather['rain_7d']} mm")
    st.caption('Weather values describe the selected location and forecast period. They are not crop-specific thresholds or a planting recommendation.')
   else:
    st.warning('Live weather could not be retrieved for this location.')
   st.subheader('Recent historical climate context')
   st.caption('NASA POWER daily point data for an approximately 90-day period ending five days before today, reflecting data availability delays. This is historical gridded climate information, not a farm weather-station measurement or a seasonal forecast.')
   with st.spinner('Retrieving recent historical climate indicators from NASA POWER...'):
    historical = get_historical_climate(planning_lat, planning_lon)
   if historical is not None and not historical.empty:
    h1, h2, h3 = st.columns(3)
    with h1: metric('Mean daily temperature', f"{historical['T2M'].mean():.1f} °C")
    with h2: metric('Accumulated precipitation', f"{historical['PRECTOTCORR'].sum():.1f} mm")
    with h3: metric('Valid data days', f"{len(historical):,}")
    climate_chart = historical.set_index('date')
    st.markdown('**Daily mean temperature (°C)**')
    st.line_chart(climate_chart[['T2M']], use_container_width=True)
    st.markdown('**Daily precipitation (mm/day)**')
    st.bar_chart(climate_chart[['PRECTOTCORR']], use_container_width=True)
    st.caption(f"Returned observations: {historical['date'].min().date()} to {historical['date'].max().date()}. Precipitation is the sum of returned daily NASA POWER values; missing or invalid days are not imputed.")
   else:
    st.info('NASA POWER did not return usable historical daily values for this point and period. No historical climate summary is displayed.')
   st.subheader('Agronomic evidence and recommendation status')
   st.caption('ECOCROP is a species-level ecological reference. It does not identify the selected cultivar and does not provide a complete farm management prescription.')
   with st.spinner('Searching the public FAO ECOCROP species reference...'):
    eco_records = search_ecocrop(crop)
   eco = None
   eco_rows = []
   if eco_records:
    eco_options = {record['_display']: record for record in eco_records}
    selected_eco_label = st.selectbox('Confirm the matching plant species', list(eco_options), key='planner_ecocrop_species')
    eco = eco_options[selected_eco_label]
    st.success(f"Species reference found: {eco.get('scientificname', 'Scientific name not listed')}")
    def _eco_value(value, unit=''):
     if value is None or (isinstance(value, float) and pd.isna(value)):
      return 'Not available'
     if isinstance(value, (int, float)):
      return f'{value:g}{unit}'
     if isinstance(value, (list, tuple)):
      return ', '.join(str(x) for x in value)
     return str(value)
    def _eco_range(low, high, unit=''):
     left, right = _eco_value(eco.get(low), unit), _eco_value(eco.get(high), unit)
     return f'{left} to {right}' if left != 'Not available' or right != 'Not available' else 'Not available'
    eco_rows = [
     {'Ecological indicator':'Optimal temperature range','ECOCROP reference':_eco_range('topmn','topmx',' °C')},
     {'Ecological indicator':'Absolute temperature limits','ECOCROP reference':_eco_range('tmin','tmax',' °C')},
     {'Ecological indicator':'Optimal annual rainfall','ECOCROP reference':_eco_range('ropmn','ropmx',' mm/year')},
     {'Ecological indicator':'Absolute annual rainfall limits','ECOCROP reference':_eco_range('rmin','rmax',' mm/year')},
     {'Ecological indicator':'Crop-cycle range','ECOCROP reference':_eco_range('gmin','gmax',' days')},
     {'Ecological indicator':'Optimal soil pH','ECOCROP reference':_eco_range('phopmn','phopmx')},
     {'Ecological indicator':'Absolute soil pH limits','ECOCROP reference':_eco_range('phmin','phmax')},
     {'Ecological indicator':'Preferred soil texture','ECOCROP reference':_eco_value(eco.get('text'))},
     {'Ecological indicator':'Climate zones','ECOCROP reference':_eco_value(eco.get('cliz'))},
    ]
    st.dataframe(pd.DataFrame(eco_rows), use_container_width=True, hide_index=True)
    st.caption(f"ECOCROP species record ID: {eco.get('ecoportcode', 'not supplied')} · [FAO ECOCROP](https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id={eco.get('ecoportcode', '')})")
    st.caption('Source data: FAO ECOCROP database, distributed through the CGIAR Climate Action Data Hub (CC BY 4.0).')
    st.warning('These are expert-compiled ecological reference values, not measured conditions at this farm or validated cultivar-specific thresholds. Missing fields remain unavailable. Annual rainfall values must not be compared directly with the 7-day forecast.')
    st.markdown('**Evidence-based environment checks**')
    observed_mean_temp = float(historical['T2M'].mean()) if historical is not None and not historical.empty else None
    environment_checks = assess_crop_environment(eco, observed_mean_temp, soil_ph if soil_ph > 0 else None)
    st.dataframe(pd.DataFrame(environment_checks), use_container_width=True, hide_index=True)
    st.caption('No overall suitability score is calculated. Temperature comparison uses the recent historical period shown above, not a full growing season. Soil pH is compared only when a value is supplied and ECOCROP provides an absolute range.')
    st.info('Annual rainfall requirements are not compared with the approximately 90-day NASA POWER record or the 7-day forecast. A valid rainfall comparison requires a matching long-term annual or crop-season climate baseline.')
    if soil_ph > 0:
     ph_min, ph_max = eco.get('phmin'), eco.get('phmax')
     ph_opt_min, ph_opt_max = eco.get('phopmn'), eco.get('phopmx')
     if all(isinstance(v, (int, float)) and not pd.isna(v) for v in [ph_min, ph_max]):
      if ph_min <= soil_ph <= ph_max:
       st.info(f'Reported soil pH {soil_ph:.1f} falls within the ECOCROP absolute pH range ({ph_min:g}–{ph_max:g}). This is a reference-range check, not a soil fertility diagnosis.')
      else:
       st.warning(f'Reported soil pH {soil_ph:.1f} is outside the ECOCROP absolute pH range ({ph_min:g}–{ph_max:g}). Verify the laboratory result and local soil conditions.')
     else:
      st.caption('ECOCROP does not provide an absolute soil pH range for this species record.')
   else:
    st.info('No confident ECOCROP species match was returned for this crop name, or the public dataset could not be reached. No ecological thresholds have been inferred.')
   st.subheader('Global crop calendar evidence')
   st.write('AgriNova AI is designed for worldwide crop planning. Crop-calendar coverage differs by source, country, crop, irrigation system, agroecological zone and reference year. No single source provides complete, current calendars for every crop worldwide.')
   st.markdown('**Global reference sources**')
   st.markdown('- [FAO Crop Calendar](https://cropcalendar.apps.fao.org/) — searchable planting and harvesting guidance for more than 100 crops in more than 50 countries, organized by agroecological zone. Coverage is not universal.')
   st.markdown('- [FAO AQUASTAT irrigated crop calendars](https://www.fao.org/aquastat/en/databases/crop-calendar/) — historical irrigated crop calendars; the underlying review covers 165 countries and around 60 irrigated crops, but availability and reliability vary by country and year.')
   st.markdown('- [FAO / IIASA GAEZ v5](https://www.fao.org/gaez/en/) — global agro-ecological assessment with updated soil, land-cover and climate inputs, crop suitability and productivity layers. The 2025 release uses a 2020 baseline and includes historical climate averages and future climate projections; outputs are model-based, not farm measurements.')
   st.markdown('- [University of Minnesota GEMS global crop-calendar API](https://gems.umn.edu/apis/crop-calendar) — global gridded planting and harvest estimates for selected crops, with a circa-2007 reference period and research-use licensing conditions.')
   st.markdown('- [World Bank / JRC-ASAP African crop calendar](https://datacatalog.worldbank.org/search/dataset/0066842/crop-calendar-for-africa) — optional Africa-only 2019 dataset for selected cereals, based on FAO calendars and satellite phenology.')
   st.caption('Reference periods and methods differ. Historical or modeled calendar information must not be presented as a current-season forecast or a cultivar-specific recommendation.')
   st.markdown('**Global agroecological and geospatial tools**')
   st.markdown('- [Open the GAEZ v5 geospatial platform](https://data.apps.fao.org/gaez/?lang=en) — explore global land, soil, climate, growing-period and crop-suitability layers.')
   st.markdown('- [Open the FAO Hand-in-Hand Geospatial Platform](https://data.apps.fao.org/) — explore FAO spatial information across crops, soils, water, climate, livestock and other sectors.')
   st.caption('These are external data portals. AgriNova AI does not yet extract a GAEZ or Hand-in-Hand pixel value automatically for the selected farm coordinates; inspect the layer metadata, spatial resolution and reference period before applying results.')
   st.markdown('**Upload and explore a crop-calendar dataset**')
   st.write('Upload a calendar file from one of the sources above, or another authoritative national agricultural source. Confirm its columns and time format below. The explorer can filter by country and crop when those fields are present.')
   calendar_file = st.file_uploader('Upload crop-calendar data (CSV or Excel)', type=['csv','xlsx'], key='planner_global_crop_calendar_file')
   if calendar_file is not None:
    try:
     if calendar_file.name.lower().endswith('.xlsx'):
      excel_book = pd.ExcelFile(calendar_file)
      sheet_name = st.selectbox('Select worksheet', excel_book.sheet_names, key='planner_calendar_sheet')
      calendar_df = pd.read_excel(excel_book, sheet_name=sheet_name)
     else:
      calendar_df = pd.read_csv(calendar_file)
     if calendar_df.empty:
      st.warning('The uploaded file contains no data rows.')
     else:
      st.caption(f'Loaded {len(calendar_df):,} rows and {len(calendar_df.columns)} columns. Review the preview and confirm each mapping; no field is assumed to be correct.')
      st.dataframe(calendar_df.head(8), use_container_width=True, hide_index=True)
      calendar_cols = ['— Not available —'] + list(calendar_df.columns)
      def _calendar_guess(candidates):
       normalized = {str(col).strip().lower().replace(' ', '_').replace('-', '_'): col for col in calendar_df.columns}
       for candidate in candidates:
        if candidate in normalized:
         return calendar_cols.index(normalized[candidate])
       return 0
      map1, map2 = st.columns(2)
      with map1:
       country_col = st.selectbox('Country column (optional)', calendar_cols, index=_calendar_guess(['country','country_name','name_0','adm0_name']), key='global_calendar_country_col')
       crop_col = st.selectbox('Crop column (optional)', calendar_cols, index=_calendar_guess(['crop','crop_name','crop_type','product']), key='global_calendar_crop_col')
       admin_col = st.selectbox('Administrative-area column (optional)', calendar_cols, index=_calendar_guess(['adm1','adm1_name','name_1','admin1','region','province']), key='global_calendar_admin_col')
      with map2:
       plant_start_col = st.selectbox('Planting start field', calendar_cols, index=_calendar_guess(['sos_s','planting_start','plant_start','planting_month','sowing_month']), key='global_calendar_plant_start')
       plant_end_col = st.selectbox('Planting end field (optional)', calendar_cols, index=_calendar_guess(['sos_e','planting_end','plant_end']), key='global_calendar_plant_end')
       harvest_start_col = st.selectbox('Harvest start field (optional)', calendar_cols, index=_calendar_guess(['eos_s','harvest_start','harvest_month']), key='global_calendar_harvest_start')
       harvest_end_col = st.selectbox('Harvest end field (optional)', calendar_cols, index=_calendar_guess(['eos_e','harvest_end']), key='global_calendar_harvest_end')
      time_format = st.selectbox('Time-field format', ['10-day dekads (1–36)','Month numbers (1–12)','Keep source values as provided'], key='global_calendar_time_format')
      if country_col != '— Not available —' or crop_col != '— Not available —':
       filtered_calendar = calendar_df.copy()
       selected_country = str(region.get('country') or '').strip() if region else ''
       if country_col != '— Not available —' and selected_country:
        country_mask = filtered_calendar[country_col].astype(str).str.casefold().str.contains(selected_country.casefold(), na=False, regex=False)
        filtered_calendar = filtered_calendar[country_mask]
       if crop_col != '— Not available —' and crop.strip():
        crop_mask = filtered_calendar[crop_col].astype(str).str.casefold().str.contains(str(crop).casefold(), na=False, regex=False)
        filtered_calendar = filtered_calendar[crop_mask]
       if admin_col != '— Not available —' and region:
        area_terms = [str(region.get(k) or '').strip() for k in ['name','admin1','admin2']]
        area_terms = [term for term in area_terms if term and term.casefold() != selected_country.casefold()]
        if area_terms:
         area_mask = pd.Series(False, index=filtered_calendar.index)
         for term in area_terms:
          area_mask |= filtered_calendar[admin_col].astype(str).str.casefold().str.contains(term.casefold(), na=False, regex=False)
         if area_mask.any():
          filtered_calendar = filtered_calendar[area_mask]
         else:
          st.caption('No administrative-area text match was found. The displayed results remain at the country or broader source level; verify geographic identifiers before relying on them.')
       if filtered_calendar.empty:
        st.info('No rows matched the selected country and crop text. Check the source naming and column mappings. No planting dates have been inferred.')
       else:
        st.success(f'{len(filtered_calendar):,} matching record(s) found in the uploaded file.')
        def _calendar_time_label(value):
         try:
          number = int(float(value))
          if time_format == '10-day dekads (1–36)':
           if number < 1 or number > 36:
            return 'Not a valid 1–36 dekad'
           month = (number - 1) // 3
           period = ['early','middle','late'][(number - 1) % 3]
           return f'{period} {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][month]} (dekad {number})'
          if time_format == 'Month numbers (1–12)':
           if number < 1 or number > 12:
            return 'Not a valid 1–12 month'
           return ["January","February","March","April","May","June","July","August","September","October","November","December"][number-1]
          return str(value)
         except (TypeError, ValueError):
          return str(value) if pd.notna(value) else 'Not available'
        calendar_display = filtered_calendar.copy()
        phase_columns = [('Planting start',plant_start_col),('Planting end',plant_end_col),('Harvest start',harvest_start_col),('Harvest end',harvest_end_col)]
        display_phase_cols = []
        for label, col in phase_columns:
         if col != '— Not available —':
          display_name = label + (' (approx.)' if time_format != 'Keep source values as provided' else '')
          calendar_display[display_name] = calendar_display[col].map(_calendar_time_label) if time_format != 'Keep source values as provided' else calendar_display[col]
          display_phase_cols.append(display_name)
        display_cols = ([country_col] if country_col != '— Not available —' else []) + ([admin_col] if admin_col != '— Not available —' else []) + ([crop_col] if crop_col != '— Not available —' else []) + display_phase_cols
        display_cols = list(dict.fromkeys(col for col in display_cols if col in calendar_display.columns))
        st.dataframe(calendar_display[display_cols] if display_cols else calendar_display, use_container_width=True, hide_index=True)
        if time_format == '10-day dekads (1–36)':
         st.caption('Dekads are approximate ten-day periods: 1–3 = January, 4–6 = February, …, 34–36 = December. These are source calendar periods, not exact dates.')
        elif time_format == 'Month numbers (1–12)':
         st.caption('Month labels are derived from numeric month values. Check the source metadata to confirm what each period represents.')
        st.caption('Source records retain their original reference period and methodology. The explorer does not convert historical records into a current-season forecast.')
      else:
       st.warning('Select at least a country column or crop column to enable filtering. You can still inspect the uploaded preview.')
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError, ImportError, OSError) as exc:
     st.error(f'Could not read this file. Check that it is a valid CSV or Excel workbook. Details: {exc}')
   report_eco_indicators = [(row['Ecological indicator'], row['ECOCROP reference']) for row in eco_rows] if eco else []
   st.session_state['farm_intelligence_report'] = {
    'location': region.get('label', 'Not available'),
    'location_precision': 'Exact farm coordinates' if use_farm_coordinates else 'Selected settlement / administrative reference point',
    'latitude': f'{planning_lat:.5f}',
    'longitude': f'{planning_lon:.5f}',
    'crop': crop,
    'variety': variety,
    'area_ha': f'{area:g}',
    'season': season,
    'production_system': system,
    'soil_ph': f'{soil_ph:.1f}' if soil_ph > 0 else 'Not supplied',
    'current_temperature_c': weather.get('current_temp') if weather else 'Not available',
    'relative_humidity_pct': weather.get('humidity') if weather else 'Not available',
    'forecast_rainfall_7d_mm': weather.get('rain_7d') if weather else 'Not available',
    'historical_mean_temperature_c': round(float(historical['T2M'].mean()), 2) if historical is not None and not historical.empty else 'Not available',
    'historical_precipitation_mm': round(float(historical['PRECTOTCORR'].sum()), 2) if historical is not None and not historical.empty else 'Not available',
    'historical_valid_days': len(historical) if historical is not None and not historical.empty else 'Not available',
    'historical_period': f"{historical['date'].min().date()} to {historical['date'].max().date()}" if historical is not None and not historical.empty else 'Not available',
    'historical_daily': [{'date': row['date'].date().isoformat(), 'temperature_c': row['T2M'], 'precipitation_mm_day': row['PRECTOTCORR']} for _, row in historical.iterrows()] if historical is not None and not historical.empty else [],
    'forecast_daily': weather.get('daily', []) if weather else [],
    'ecocrop_scientific_name': eco.get('scientificname', 'Not listed') if eco else 'Not matched',
    'ecocrop_record_id': eco.get('ecoportcode', 'Not available') if eco else 'Not available',
    'ecocrop_indicators': report_eco_indicators,
   }
   st.info('AgriNova AI withholds unsupported cultivar-specific planting dates, spacing, seed rates, fertilizer doses, irrigation schedules and yield estimates rather than inventing them.')
 if st.session_state.get('farm_intelligence_report'):
  st.divider()
  st.subheader('Download farm intelligence report')
  st.caption('Exports the profile and evidence available for this submission. Missing data remain labelled as unavailable; no unsupported agronomic prescription is added.')
  report_data = st.session_state['farm_intelligence_report']
  dl1, dl2 = st.columns(2)
  with dl1:
   st.download_button('Download PDF report', data=build_farm_report_pdf(report_data), file_name='agrinova_farm_intelligence_report.pdf', mime='application/pdf', use_container_width=True)
  with dl2:
   st.download_button('Download CSV data', data=build_farm_report_csv(report_data), file_name='agrinova_farm_intelligence_report.csv', mime='text/csv', use_container_width=True)
elif page=='Spatial Evidence Explorer':
 st.markdown('<div class="hero"><h1>🗺️ Spatial Evidence Explorer</h1><p>Map farm or field observations and compare them with selected species-level ecological reference ranges.</p></div>',unsafe_allow_html=True)
 st.warning('This workspace maps coordinates and measurements supplied in your file. It does not automatically download or sample GAEZ or SoilGrids raster cells. Do not treat the map as a validated crop-suitability classification.')
 crop_name = st.text_input('Crop or plant name for ECOCROP lookup', placeholder='e.g. maize, sorghum, sesame')
 eco_record = None
 if len(crop_name.strip()) >= 2:
  with st.spinner('Searching the ECOCROP species reference...'):
   spatial_eco_matches = search_ecocrop(crop_name)
  if spatial_eco_matches:
   eco_options = {record['_display']: record for record in spatial_eco_matches}
   eco_label = st.selectbox('Confirm species reference', list(eco_options), key='spatial_eco_species')
   eco_record = eco_options[eco_label]
   st.caption(f"Species-level reference: {eco_record.get('scientificname', 'Scientific name not listed')}. This is not a cultivar-specific profile.")
  else:
   st.info('No matching ECOCROP record was returned. Coordinates can still be mapped, but ecological comparisons will not be shown.')
 spatial_file = st.file_uploader('Upload geospatial observations (CSV or Excel)', type=['csv','xlsx'], key='spatial_observations_file')
 if spatial_file is not None:
  try:
   if spatial_file.name.lower().endswith('.xlsx'):
    spatial_book = pd.ExcelFile(spatial_file)
    spatial_sheet = st.selectbox('Select worksheet', spatial_book.sheet_names, key='spatial_observations_sheet')
    spatial_frame = pd.read_excel(spatial_book, sheet_name=spatial_sheet)
   else:
    spatial_file.seek(0)
    spatial_frame = pd.read_csv(spatial_file)
   if spatial_frame.empty:
    st.warning('The uploaded file contains no records.')
   else:
    st.caption(f'Loaded {len(spatial_frame):,} rows. Map the coordinate columns and any available environmental measurements.')
    st.dataframe(spatial_frame.head(8), use_container_width=True, hide_index=True)
    spatial_columns = ['— Not mapped —'] + [str(column) for column in spatial_frame.columns]
    coord1, coord2 = st.columns(2)
    with coord1:
     lat_col = st.selectbox('Latitude column (required)', spatial_columns, key='spatial_lat_col')
     temp_col = st.selectbox('Mean temperature column in °C (optional)', spatial_columns, key='spatial_temp_col')
    with coord2:
     lon_col = st.selectbox('Longitude column (required)', spatial_columns, key='spatial_lon_col')
     ph_col = st.selectbox('Soil pH column (optional)', spatial_columns, key='spatial_ph_col')
    if lat_col != '— Not mapped —' and lon_col != '— Not mapped —':
     mapped_spatial, spatial_warnings = normalize_spatial_observations(
      spatial_frame, lat_col, lon_col,
      temp_col if temp_col != '— Not mapped —' else None,
      ph_col if ph_col != '— Not mapped —' else None,
     )
     for warning in spatial_warnings:
      st.warning(warning)
     if not mapped_spatial.empty:
      st.success(f"Validated {len(mapped_spatial):,} georeferenced record(s).")
      if eco_record is not None:
       point_results = []
       for _, point in mapped_spatial.iterrows():
        checks = assess_crop_environment(
         eco_record,
         point.get('mean_temperature_c'),
         point.get('soil_ph'),
        )
        for check in checks:
         point_results.append({
          'Source row': int(point['source_row']),
          'Latitude': point['latitude'],
          'Longitude': point['longitude'],
          **check,
         })
       comparison_frame = pd.DataFrame(point_results)
       st.markdown('**Point-level ecological reference checks**')
       st.dataframe(comparison_frame, use_container_width=True, hide_index=True)
       st.caption('Each indicator is assessed separately. Temperature observations must represent a period comparable to the crop requirement; short-window means are contextual only. Soil pH interpretation depends on sampling and laboratory method.')
      map_center = [mapped_spatial['latitude'].mean(), mapped_spatial['longitude'].mean()]
      spatial_map = folium.Map(location=map_center, zoom_start=5, control_scale=True)
      for _, point in mapped_spatial.iterrows():
       details = [f"Source row: {int(point['source_row'])}", f"Coordinates: {point['latitude']:.5f}, {point['longitude']:.5f}"]
       if pd.notna(point.get('mean_temperature_c')):
        details.append(f"Mean temperature: {point['mean_temperature_c']:.1f} °C")
       if pd.notna(point.get('soil_ph')):
        details.append(f"Soil pH: {point['soil_ph']:.1f}")
       if eco_record is not None:
        checks = assess_crop_environment(eco_record, point.get('mean_temperature_c'), point.get('soil_ph'))
        details.extend([f"{check['Indicator']}: {check['Comparison']}" for check in checks])
       folium.CircleMarker(
        location=[point['latitude'], point['longitude']],
        radius=6, color='#16845B', fill=True, fill_color='#16845B',
        fill_opacity=0.75, tooltip=f"Record {int(point['source_row'])}",
        popup=folium.Popup('<br>'.join(details), max_width=320),
       ).add_to(spatial_map)
      st.subheader('Mapped observation points')
      st_folium(spatial_map, height=520, use_container_width=True, key='spatial_evidence_map')
      st.caption('Map markers show supplied observation coordinates only. Marker color does not indicate suitability, risk or crop performance.')
      st.download_button('Download validated spatial observations (CSV)', data=mapped_spatial.to_csv(index=False).encode('utf-8-sig'), file_name='agrinova_validated_spatial_observations.csv', mime='text/csv', key='spatial_observations_download')
    else:
     st.info('Select valid latitude and longitude columns to validate and map records.')
  except (ValueError, OSError, ImportError, UnicodeDecodeError, pd.errors.ParserError) as error:
   st.error(f'Could not read the uploaded geospatial file: {error}. Check the CSV or Excel format.')
 st.markdown('**Preparing source data**')
 st.markdown('- Export point or sample data from your GIS workflow with latitude and longitude columns.\n- GAEZ and SoilGrids downloads may be gridded raster data; convert or sample them using a GIS tool before uploading point observations.\n- Keep source names, units, depth, dates, spatial resolution and reference period with the dataset.\n- Do not combine measurements from different soil depths or incompatible laboratory methods as if they were equivalent.')
 st.caption('This first spatial workflow accepts point observations in CSV or Excel. Direct raster ingestion, automatic GAEZ/SoilGrids sampling and polygon-based farm boundaries are not yet implemented.')
elif page=='Soil Health':
 st.markdown('<div class="hero"><h1>🧪 Soil Health</h1><p>Explore global modeled soil information and interpret your own laboratory measurements.</p></div>',unsafe_allow_html=True)
 st.subheader('Global modeled soil information')
 st.caption('SoilGrids provides global 250 m soil-property predictions at six standard depth intervals. These are model estimates, not measurements taken on your farm.')
 soil_location = global_location_picker("soilgrids", "Search the farm location to explore SoilGrids (optional)")
 if soil_location:
  st.write(f"**Selected reference point:** {soil_location['label']}")
  st.write(f"**Coordinates:** {soil_location['latitude']:.5f}°, {soil_location['longitude']:.5f}°")
  st.markdown("[Open the SoilGrids global map](https://soilgrids.org/) and use the coordinates above to inspect the selected area.")
 st.warning('The ISRIC SoilGrids REST point-query API is currently temporarily paused by its provider. AgriNova AI therefore does not display or invent SoilGrids point values. Use the official map or WMS/WCS services for visual exploration and data access.')
 st.markdown('[SoilGrids map](https://soilgrids.org/) · [Official data access guidance](https://docs.isric.org/globaldata/soilgrids/index.html) · [ISRIC WMS/WCS services](https://maps.isric.org/)')
 st.caption('Available modeled properties include pH, soil organic carbon, bulk density, coarse fragments, sand, silt, clay, cation-exchange capacity and total nitrogen. Standard depths: 0–5, 5–15, 15–30, 30–60, 60–100 and 100–200 cm. Published map resolution is 250 m; predictions include a 90% uncertainty interval. Source: ISRIC SoilGrids, CC BY 4.0.')
 st.divider()
 st.subheader('Interpret your soil test results')
 st.info('Enter only values from a soil laboratory or field test. For every numeric field, enter 0 if the measurement is not available; missing values will be excluded from the interpretation.')
 with st.form('soil'):
  a,b,c=st.columns(3)
  with a:
   ph=st.number_input('Soil pH (0 = not tested)',0.,14.,0.0,.1)
   organic=st.number_input('Organic matter (%) (0 = not tested)',0.,100.,0.0,.1)
  with b:
   ec=st.number_input('Electrical conductivity (dS/m) (0 = not tested)',0.,100.,0.0,.1)
   n=st.number_input('Nitrogen (mg/kg) (0 = not tested)',0.,value=0.)
  with c:
   p=st.number_input('Available phosphorus (mg/kg) (0 = not tested)',0.,value=0.)
   k=st.number_input('Available potassium (mg/kg) (0 = not tested)',0.,value=0.)
  crop=crop_plant_picker('soil', 'Crop or plant')
  submit=st.form_submit_button('Assess measured soil indicators')
 if submit:
  measured = any(value > 0 for value in (ph, organic, ec, n, p, k))
  if not measured:
   st.info('No soil measurements were entered. Add at least one tested value to receive an interpretation.')
  else:
   results=assess_soil(ph or None,organic or None,ec or None,n or None,p or None,k or None,crop)
   for label,desc in results: st.markdown(f'**{label}:** {desc}')
   st.warning('Interpretation depends on laboratory method, soil texture and regional calibration. SoilGrids modeled values are not substitutes for laboratory results. Use a recognized soil laboratory and local agronomic advice before fertilizer or amendment decisions.')
 st.divider()
 st.subheader('Import a soil laboratory dataset')
 st.caption('Upload a CSV or Excel file containing soil-test results. You choose which columns represent each measurement. The importer preserves sample records, reports invalid values and does not fill missing measurements.')
 uploaded_soil = st.file_uploader('Upload soil laboratory results', type=['csv', 'xlsx'], key='soil_lab_upload')
 if uploaded_soil is not None:
  try:
   if uploaded_soil.name.lower().endswith('.csv'):
    uploaded_soil.seek(0)
    soil_workbook = None
    soil_frame = pd.read_csv(uploaded_soil)
    selected_sheet = None
   else:
    uploaded_soil.seek(0)
    soil_workbook = pd.ExcelFile(uploaded_soil)
    selected_sheet = st.selectbox('Excel worksheet', soil_workbook.sheet_names, key='soil_lab_sheet')
    soil_frame = soil_workbook.parse(selected_sheet)
   if soil_frame.empty:
    st.warning('The selected file or worksheet contains no rows.')
   else:
    st.write(f'**Uploaded records:** {len(soil_frame):,} rows · **Columns:** {len(soil_frame.columns):,}')
    st.dataframe(soil_frame.head(8), use_container_width=True, hide_index=True)
    st.markdown('**Map the columns in your file**')
    column_options = ['— Not mapped —'] + [str(column) for column in soil_frame.columns]
    field_specs = {**OPTIONAL_FIELDS, **{key: value['label'] + ' (' + value['unit'] + ')' for key, value in MEASUREMENTS.items()}}
    mapping = {}
    map_fields = list(OPTIONAL_FIELDS) + list(MEASUREMENTS)
    map_cols = st.columns(2)
    for index, field in enumerate(map_fields):
     with map_cols[index % 2]:
      chosen = st.selectbox(field_specs[field], column_options, key=f'soil_map_{field}')
      mapping[field] = None if chosen == '— Not mapped —' else chosen
    if st.button('Validate and import soil results', key='soil_lab_validate'):
     cleaned, validation = normalize_soil_lab_data(soil_frame, mapping)
     if validation['errors']:
      for message in validation['errors']: st.error(message)
     elif cleaned.empty:
      st.warning('No usable measurement records were found in the selected worksheet.')
     else:
      st.success(f"Imported {validation['rows_with_measurements']:,} record(s) containing at least one valid measurement.")
      st.caption('The original worksheet is not modified. Rows without valid mapped measurements are excluded from the analysis table.')
      for warning in validation['warnings']: st.warning(warning)
      summary = soil_lab_summary(cleaned)
      if not summary.empty:
       st.markdown('**Descriptive summary of uploaded laboratory values**')
       st.dataframe(summary, use_container_width=True, hide_index=True)
      st.markdown('**Validated sample records**')
      st.dataframe(cleaned, use_container_width=True, hide_index=True)
      csv_export = cleaned.to_csv(index=False).encode('utf-8-sig')
      st.download_button('Download validated soil dataset (CSV)', data=csv_export, file_name='agrinova_validated_soil_results.csv', mime='text/csv', key='soil_lab_download')
      st.caption('Summary statistics describe only the uploaded samples. They are not regional soil classifications, crop-specific thresholds or fertilizer recommendations.')
      comparison_fields = [field for field in OPTIONAL_FIELDS if field in cleaned and cleaned[field].notna().nunique() > 1]
      if comparison_fields:
       st.markdown('**Compare samples by location, depth, date or sample group**')
       group_by = st.selectbox('Group samples by', comparison_fields, key='soil_lab_group_by')
       grouped_summary = soil_lab_group_summary(cleaned, group_by)
       if not grouped_summary.empty:
        st.dataframe(grouped_summary, use_container_width=True, hide_index=True)
        st.caption('Grouped medians and sample counts are descriptive summaries. Differences may reflect sampling design, laboratory methods or soil variability.')
      chart_fields = [field for field in MEASUREMENTS if field in cleaned and cleaned[field].notna().sum() > 1]
      if chart_fields:
       st.markdown('**Measurement distributions**')
       for field in chart_fields:
        values = cleaned.loc[cleaned[field].notna(), field]
        st.markdown(f"**{MEASUREMENTS[field]['label']} ({MEASUREMENTS[field]['unit']})**")
        if 'depth_cm' in cleaned and cleaned['depth_cm'].notna().nunique() > 1:
         chart_data = cleaned.loc[cleaned[field].notna() & cleaned['depth_cm'].notna()]
         if not chart_data.empty:
          fig = px.scatter(chart_data, x='depth_cm', y=field, color='location' if 'location' in chart_data and chart_data['location'].nunique() > 1 else None, hover_data=['sample_id'] if 'sample_id' in chart_data else None, labels={'depth_cm':'Sampling depth (cm)',field:MEASUREMENTS[field]['label']})
          fig.update_xaxes(autorange='reversed')
          st.plotly_chart(fig, use_container_width=True)
        elif 'location' in cleaned and cleaned['location'].notna().nunique() > 1:
         chart_data = cleaned.loc[cleaned[field].notna() & cleaned['location'].notna()]
         fig = px.box(chart_data, x='location', y=field, points='all', labels={'location':'Sample location',field:MEASUREMENTS[field]['label']})
         st.plotly_chart(fig, use_container_width=True)
        else:
         st.plotly_chart(px.histogram(values, nbins=20, labels={'value':MEASUREMENTS[field]['unit']}, title='Distribution across uploaded samples'), use_container_width=True)
  except (ValueError, OSError, ImportError, UnicodeDecodeError) as error:
   st.error(f'Could not read this soil dataset: {error}. Check the file format and try again.')
elif page=='Agri Knowledge Assistant':
 st.markdown('<div class="hero"><h1>📚 Agricultural Knowledge Assistant</h1><p>Search curated agricultural knowledge locally using TF-IDF text similarity.</p></div>',unsafe_allow_html=True)
 q=st.text_input('Ask an agricultural question'); category=st.selectbox('Topic',['All']+sorted({x['category'] for x in KNOWLEDGE}))
 if st.button('Search') and q.strip():
  results=search_knowledge(q,category)
  if results:
   for item in results:
    with st.expander(item['title'],expanded=True): st.write(item['answer']); st.caption('Source: '+item['source'])
  else: st.info('No close match; try other keywords or browse topics below.')
 st.subheader('Knowledge library')
 for item in KNOWLEDGE:
  if category=='All' or item['category']==category:
   with st.expander(item['title']): st.write(item['answer']); st.caption('Source: '+item['source'])
elif page=='Data Sources & Methodology':
 st.markdown('<div class="hero"><h1>🗂️ Data Sources & Methodology</h1><p>Transparent source coverage, access notes and limitations.</p></div>',unsafe_allow_html=True)
 st.dataframe(pd.DataFrame(DATA_SOURCES),use_container_width=True,hide_index=True,column_config={'URL':st.column_config.LinkColumn('Source website')})
 st.subheader('Interpretation rules')
 st.markdown('- Prefer Somalia-specific observed data when available.\n- Clearly label regional estimates and global modeled information.\n- Satellite observations are not ground observations.\n- Soil maps do not replace farm-level laboratory tests.\n- Check licenses and terms before commercial reuse.')
 st.info('Included functions use public/free access services where possible. Some source portals may require free registration or have product-specific terms.')
st.divider(); st.caption('AgriNova AI • Agricultural Intelligence Platform • Python + Streamlit • Free-data-first')
