import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from modules.data_sources import get_weather, get_historical_climate, search_global_locations, search_ecocrop, DATA_SOURCES
from modules.agronomy import CROPS, get_crop_guidance, assess_soil, screen_crop_symptoms, search_knowledge, KNOWLEDGE

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
 page=st.radio('WORKSPACE',['Overview','Crop Health Screening','Weather & Climate','Crop Planner','Soil Health','Agri Knowledge Assistant','Data Sources & Methodology'])
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
   st.subheader('Agronomic evidence and recommendation status')
   st.caption('ECOCROP is a species-level ecological reference. It does not identify the selected cultivar and does not provide a complete farm management prescription.')
   with st.spinner('Searching the public FAO ECOCROP species reference...'):
    eco_records = search_ecocrop(crop)
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
   st.subheader('Crop calendar evidence')
   st.markdown('**African crop calendar dataset (World Bank / JRC-ASAP)**')
   st.write('A public 2019 dataset based on FAO crop calendars provides planting, growing and harvesting dekads for sorghum, millet, barley, maize and wheat at national and subnational levels for most African countries. The source includes only records that matched the ASAP satellite-derived phenology; it does not guarantee coverage for every crop or administrative area.')
   st.markdown('[Open dataset and download CSV files](https://datacatalog.worldbank.org/search/dataset/0066842/crop-calendar-for-africa) · [View JRC-ASAP download documentation](https://agricultural-production-hotspots.ec.europa.eu/download.php)')
   st.caption('The calendar dataset describes 2019 timing and uses 10-day dekads, not exact daily dates. AgriNova AI does not treat it as a current-season forecast or a cultivar-specific recommendation.')
   st.markdown('**Explore the source data (CSV upload)**')
   st.write('Download the national or subnational CSV from the World Bank page above, then upload it here. Because source files can use different administrative labels, confirm the relevant columns before filtering.')
   calendar_file = st.file_uploader('Upload World Bank / JRC-ASAP crop-calendar CSV', type=['csv'], key='planner_crop_calendar_csv')
   if calendar_file is not None:
    try:
     calendar_df = pd.read_csv(calendar_file)
     if calendar_df.empty:
      st.warning('The uploaded CSV contains no data rows.')
     else:
      st.caption(f'Loaded {len(calendar_df):,} rows and {len(calendar_df.columns)} columns. Confirm the column mappings below; no field is assumed to be correct.')
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
       country_col = st.selectbox('Country column', calendar_cols, index=_calendar_guess(['country','country_name','name_0','adm0_name']), key='calendar_country_col')
       crop_col = st.selectbox('Crop column', calendar_cols, index=_calendar_guess(['crop','crop_name','crop_type','product']), key='calendar_crop_col')
       admin_col = st.selectbox('Administrative-area column (optional)', calendar_cols, index=_calendar_guess(['adm1','adm1_name','name_1','admin1','region','province']), key='calendar_admin_col')
      with map2:
       plant_start_col = st.selectbox('Planting start dekad', calendar_cols, index=_calendar_guess(['sos_s','planting_start','plant_start']), key='calendar_plant_start')
       plant_end_col = st.selectbox('Planting end dekad', calendar_cols, index=_calendar_guess(['sos_e','planting_end','plant_end']), key='calendar_plant_end')
       growth_start_col = st.selectbox('Growth start dekad (optional)', calendar_cols, index=_calendar_guess(['sos_e','growth_start']), key='calendar_growth_start')
       growth_end_col = st.selectbox('Growth end dekad (optional)', calendar_cols, index=_calendar_guess(['eos_s','growth_end']), key='calendar_growth_end')
       harvest_start_col = st.selectbox('Harvest start dekad (optional)', calendar_cols, index=_calendar_guess(['eos_s','harvest_start']), key='calendar_harvest_start')
       harvest_end_col = st.selectbox('Harvest end dekad (optional)', calendar_cols, index=_calendar_guess(['eos_e','harvest_end']), key='calendar_harvest_end')
      if country_col != '— Not available —' and crop_col != '— Not available —':
       filtered_calendar = calendar_df.copy()
       selected_country = str(region.get('country') or '').strip()
       if selected_country:
        country_mask = filtered_calendar[country_col].astype(str).str.casefold().str.contains(selected_country.casefold(), na=False, regex=False)
        filtered_calendar = filtered_calendar[country_mask]
       if admin_col != '— Not available —':
        area_terms = [str(region.get(k) or '').strip() for k in ['name','admin1','admin2']]
        area_terms = [term for term in area_terms if term and term.casefold() != selected_country.casefold()]
        if area_terms:
         area_mask = pd.Series(False, index=filtered_calendar.index)
         for term in area_terms:
          area_mask |= filtered_calendar[admin_col].astype(str).str.casefold().str.contains(term.casefold(), na=False, regex=False)
         if area_mask.any():
          filtered_calendar = filtered_calendar[area_mask]
         else:
          st.caption('No administrative-area text match was found. Showing country-level matches only; verify the source geography before using the records.')
       crop_mask = filtered_calendar[crop_col].astype(str).str.casefold().str.contains(str(crop).casefold(), na=False, regex=False)
       filtered_calendar = filtered_calendar[crop_mask]
       if filtered_calendar.empty:
        st.info('No rows matched the selected country and crop text. Check the source naming and column mappings; no planting dates have been inferred.')
       else:
        st.success(f'{len(filtered_calendar):,} matching calendar record(s) found in the uploaded file.')
        def _dekad_label(value):
         try:
          number = int(float(value))
          if number < 1 or number > 36:
           return 'Not a valid 1–36 dekad'
          month = (number - 1) // 3
          period = ['early','middle','late'][(number - 1) % 3]
          return f'{period} {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][month]} (dekad {number})'
         except (TypeError, ValueError):
          return 'Not available / non-numeric'
        calendar_display = filtered_calendar.copy()
        phase_columns = [('Planting start',plant_start_col),('Planting end',plant_end_col),('Growth start',growth_start_col),('Growth end',growth_end_col),('Harvest start',harvest_start_col),('Harvest end',harvest_end_col)]
        for label, col in phase_columns:
         if col != '— Not available —':
          calendar_display[label + ' (approx.)'] = calendar_display[col].map(_dekad_label)
        display_cols = [country_col,crop_col] + ([admin_col] if admin_col != '— Not available —' else []) + [label + ' (approx.)' for label,col in phase_columns if col != '— Not available —']
        display_cols = list(dict.fromkeys(col for col in display_cols if col in calendar_display.columns))
        st.dataframe(calendar_display[display_cols], use_container_width=True, hide_index=True)
        st.caption('Dekads are approximate ten-day periods: 1–3 = January, 4–6 = February, …, 34–36 = December. These are source calendar periods, not exact dates or a current-season forecast. This display does not calculate crop duration.')
      else:
       st.warning('Select both a country column and a crop column to filter the uploaded data.')
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
     st.error(f'Could not read this CSV. Check that it is a valid comma-separated file. Details: {exc}')
   st.markdown('**Other authoritative references for future crop- and location-specific guidance:**')
   st.markdown('- [FAO Crop Calendar](https://cropcalendar.apps.fao.org/) — planting and harvesting periods by country and agroecological zone where records exist.')
   st.markdown('- [FAO ECOCROP / GAEZ](https://gaez.fao.org/pages/ecocrop) — broader crop ecological characteristics.')
   st.markdown('- [FAO AQUASTAT irrigated crop calendars](https://www.fao.org/aquastat/en/databases/crop-calendar/) — historical country-level irrigated crop calendar information where available.')
   st.info('AgriNova AI still withholds cultivar-specific planting dates, spacing, seed rates, fertilizer doses, irrigation schedules and yield estimates until authoritative matching data is available.')
elif page=='Soil Health':
 st.markdown('<div class="hero"><h1>🧪 Soil Health</h1><p>Interpret soil measurements supplied by the user.</p></div>',unsafe_allow_html=True)
 st.info('Use laboratory or field-test results. The app does not invent missing measurements or fertilizer rates.')
 with st.form('soil'):
  a,b,c=st.columns(3)
  with a: ph=st.number_input('Soil pH',0.,14.,6.5,.1); organic=st.number_input('Organic matter (%)',0.,100.,1.5,.1)
  with b: ec=st.number_input('Electrical conductivity (dS/m)',0.,100.,.5,.1); n=st.number_input('Nitrogen (mg/kg)',0.,value=20.)
  with c: p=st.number_input('Available phosphorus (mg/kg)',0.,value=10.); k=st.number_input('Available potassium (mg/kg)',0.,value=100.)
  crop=crop_plant_picker('soil', 'Crop or plant'); submit=st.form_submit_button('Assess soil indicators')
 if submit:
  for label,desc in assess_soil(ph,organic,ec,n,p,k,crop): st.markdown(f'**{label}:** {desc}')
  st.warning('Interpretation depends on laboratory method, soil texture and regional calibration. Use a recognized soil laboratory for fertilizer decisions.')
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
