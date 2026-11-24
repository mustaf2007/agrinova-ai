import streamlit as st
import json
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from modules.data_sources import get_weather, get_historical_climate, search_global_locations, search_ecocrop, DATA_SOURCES
from modules.agronomy import CROPS, get_crop_guidance, assess_soil, screen_crop_symptoms, search_knowledge, KNOWLEDGE
from modules.reporting import build_farm_report_csv, build_farm_report_pdf
from modules.soil_lab import MEASUREMENTS, OPTIONAL_FIELDS, normalize_soil_lab_data, soil_lab_summary, soil_lab_group_summary
from modules.crop_suitability import assess_crop_environment, normalize_spatial_observations, validate_geojson_boundaries
from modules.soilgrids_wcs import fetch_nitrogen_coverages, fetch_nitrogen_geotiff, analyze_nitrogen_geotiff, SOILGRIDS_NITROGEN_WCS, SOILGRIDS_WCS_DOCS

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
st.markdown(f'''<style>
/* AgriNova visual system: responsive, theme-aware and dependency-free */
:root{{--agri-accent:{t['accent']};--agri-soft:{t['soft']};--agri-panel:{t['panel']};--agri-border:{t['border']};--agri-text:{t['text']};--agri-muted:{t['muted']}}}
html,body,[class*="css"]{{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
.block-container{{padding-bottom:3rem}}
[data-testid="stSidebar"]{{box-shadow:5px 0 24px rgba(20,50,35,.045)}}
[data-testid="stSidebar"] [data-testid="stRadio"] label{{padding:.48rem .65rem;border-radius:10px;transition:background .18s ease}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{{background:{t['soft']}}}
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"]{{background:{t['soft']};font-weight:700}}
.hero{{position:relative;overflow:hidden;background:linear-gradient(115deg,{t['soft']} 0%,{t['panel']} 58%,{t['soft']} 130%);border:1px solid {t['border']};border-radius:22px;padding:1.7rem 1.8rem;margin:.15rem 0 1.35rem;box-shadow:0 8px 26px rgba(25,60,40,.045)}}
.hero:after{{content:"";position:absolute;width:190px;height:190px;border-radius:50%;right:-55px;top:-85px;background:{t['accent']};opacity:.075;pointer-events:none}}
.agri-hero{{position:relative;isolation:isolate;display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:310px;overflow:hidden;padding:2.1rem 2.3rem;margin:.15rem 0 1.8rem;border-radius:25px;border:1px solid {t['border']};background:linear-gradient(112deg,{t['soft']} 0%,{t['panel']} 57%,{t['soft']} 130%);box-shadow:0 12px 34px rgba(24,60,38,.07)}}
.agri-hero-copy{{position:relative;z-index:3;max-width:650px}}
.agri-eyebrow,.agri-kicker{{font-size:.72rem;font-weight:800;letter-spacing:.13em;color:{t['accent']};margin-bottom:.8rem}}
.agri-hero h1{{font-size:clamp(2rem,4vw,3.35rem);line-height:1.04;letter-spacing:-.055em;font-weight:850;margin:0 0 .85rem}}
.agri-hero h1 span{{color:{t['accent']}}}
.agri-hero p{{font-size:1.02rem;line-height:1.65;color:{t['muted']};max-width:590px;margin:0 0 1.2rem}}
.agri-tags{{display:flex;flex-wrap:wrap;gap:.5rem}}
.agri-tags span{{font-size:.78rem;font-weight:650;color:{t['text']};background:{t['panel']};border:1px solid {t['border']};padding:.48rem .7rem;border-radius:999px}}
.agri-hero-art{{position:absolute;z-index:1;right:0;bottom:0;width:43%;height:100%;overflow:hidden;background:linear-gradient(180deg,transparent 25%,{t['soft']} 100%);opacity:.95}}
.agri-sun{{position:absolute;right:22%;top:12%;width:88px;height:88px;border-radius:50%;background:linear-gradient(135deg,#F7D98A,#E9B95E);opacity:.8;box-shadow:0 0 0 18px rgba(232,190,99,.10),0 0 0 38px rgba(232,190,99,.06)}}
.agri-field{{position:absolute;left:-10%;width:125%;border-radius:50% 50% 0 0 / 30% 30% 0 0;transform:rotate(-7deg)}}
.field-back{{height:43%;bottom:15%;background:linear-gradient(90deg,#A7C78F,#6F9E69);opacity:.48}}
.field-mid{{height:37%;bottom:4%;background:repeating-linear-gradient(105deg,transparent 0 17px,rgba(255,255,255,.16) 18px 20px),linear-gradient(90deg,#6E9C62,#39784B);opacity:.8}}
.field-front{{height:29%;bottom:-12%;background:repeating-linear-gradient(105deg,transparent 0 14px,rgba(255,255,255,.18) 15px 17px),linear-gradient(90deg,#477B4A,#205D3B)}}
.agri-stalk{{position:absolute;z-index:2;font-size:3rem;filter:drop-shadow(0 5px 6px rgba(25,65,35,.15))}}
.stalk-one{{right:23%;bottom:28%;font-size:4.4rem;transform:rotate(-9deg)}}.stalk-two{{right:8%;bottom:18%;font-size:3.6rem;transform:rotate(10deg)}}.stalk-three{{right:39%;bottom:14%;font-size:2.9rem}}
.agri-section-intro{{display:flex;justify-content:space-between;align-items:end;gap:1rem;margin:0 0 .9rem}}
.agri-section-intro h2{{margin:0;font-size:1.45rem}}
.agri-section-intro p{{color:{t['muted']};font-size:.86rem;margin:0 0 .15rem}}
.agri-feature-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;margin:0 0 1.6rem}}
.agri-feature{{display:flex;align-items:center;gap:.85rem;padding:1rem;border-radius:15px;border:1px solid {t['border']};background:{t['panel']};box-shadow:0 4px 15px rgba(20,50,35,.035);transition:transform .18s ease,box-shadow .18s ease}}
.agri-feature:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(20,50,35,.08)}}
.agri-feature-icon{{display:grid;place-items:center;flex:0 0 44px;height:44px;border-radius:13px;background:{t['soft']};font-size:1.35rem}}
.agri-feature b{{display:block;color:{t['text']};font-size:.92rem;margin-bottom:.2rem}}
.agri-feature small{{display:block;color:{t['muted']};font-size:.76rem;line-height:1.45}}

.module-eyebrow{{font-size:.68rem;font-weight:800;letter-spacing:.13em;color:{t['accent']};margin-bottom:.55rem;position:relative;z-index:1}}
.hero{{position:relative;isolation:isolate;overflow:hidden}}
.hero:before{{content:"🌱";position:absolute;right:2.1rem;bottom:-.8rem;font-size:5.5rem;line-height:1;opacity:.12;transform:rotate(-13deg);pointer-events:none}}
.hero h1,.hero p{{position:relative;z-index:1}}
.hero h1{{padding-right:4rem}}
@media(max-width:600px){{.hero:before{{right:.8rem;font-size:3.6rem}}.hero h1{{padding-right:2.8rem}}}}

.hero h1{{font-size:clamp(1.65rem,3vw,2.25rem);font-weight:800;letter-spacing:-.045em;margin:0 0 .35rem}}
.hero p{{font-size:1rem;line-height:1.55;max-width:850px;margin:0;color:{t['muted']}}}
.metric-card{{border-radius:17px;padding:1.05rem 1.1rem;box-shadow:0 5px 18px rgba(20,50,35,.045);transition:transform .18s ease,box-shadow .18s ease}}
.metric-card:hover{{transform:translateY(-2px);box-shadow:0 10px 25px rgba(20,50,35,.09)}}
.metric-label{{letter-spacing:.025em}}
.metric-value{{font-size:clamp(1.25rem,2vw,1.65rem);letter-spacing:-.035em;margin:.28rem 0;overflow-wrap:anywhere}}
h2{{font-weight:750;letter-spacing:-.025em;margin-top:1.25rem}}
h3{{font-weight:700;letter-spacing:-.018em}}
[data-testid="stVerticalBlock"] [data-testid="stExpander"]{{border:1px solid {t['border']};border-radius:13px;background:{t['panel']};overflow:hidden}}
[data-testid="stExpander"] summary{{font-weight:650}}
.stButton>button,[data-testid="stDownloadButton"] button,[data-testid="stFormSubmitButton"] button{{min-height:2.65rem;border-radius:11px;font-weight:650;letter-spacing:.005em;box-shadow:0 3px 9px rgba(20,60,40,.08);transition:filter .18s ease,transform .18s ease,box-shadow .18s ease}}
.stButton>button:hover,[data-testid="stDownloadButton"] button:hover,[data-testid="stFormSubmitButton"] button:hover{{filter:brightness(1.06);transform:translateY(-1px);box-shadow:0 6px 15px rgba(20,60,40,.13)}}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] [data-baseweb="select"]>div{{border-radius:10px}}
[data-testid="stFileUploader"]{{border:1px dashed {t['accent']};border-radius:14px;background:{t['soft']};padding:.35rem}}
[data-testid="stDataFrame"], [data-testid="stTable"]{{border:1px solid {t['border']};border-radius:12px;overflow:hidden}}
[data-testid="stAlert"]{{border-radius:12px}}
[data-testid="stPlotlyChart"]{{border:1px solid {t['border']};border-radius:15px;padding:.4rem;background:{t['panel']}}}
[data-testid="stTabs"] button{{font-weight:650}}
hr{{margin:1.35rem 0}}
::selection{{background:{t['soft']};color:{t['text']}}}
::-webkit-scrollbar{{width:9px;height:9px}}
::-webkit-scrollbar-thumb{{background:{t['border']};border-radius:10px}}
@media(max-width:768px){{.block-container{{padding-left:1rem;padding-right:1rem;padding-top:1rem}}.hero{{padding:1.25rem;border-radius:17px}}.metric-card{{min-height:90px;padding:.85rem}}.agri-hero{{min-height:330px;padding:1.35rem;border-radius:18px;align-items:flex-start}}.agri-hero-art{{width:100%;height:46%;opacity:.65}}.agri-hero-copy{{max-width:100%}}.agri-feature-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.agri-section-intro{{display:block}}.agri-section-intro p{{margin-top:.4rem}}}}
@media(max-width:480px){{.agri-feature-grid{{grid-template-columns:1fr}}.agri-hero h1{{font-size:2rem}}.agri-tags span{{font-size:.7rem}}}}
</style>''',unsafe_allow_html=True)
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
 st.markdown("""
 <section class="agri-hero">
   <div class="agri-hero-copy">
     <div class="agri-eyebrow">🌾 AGRICULTURAL INTELLIGENCE &amp; DECISION SUPPORT</div>
     <h1>Evidence for better<br><span>agricultural decisions.</span></h1>
     <p>Explore crop health, weather and climate, soil information, spatial observations and agronomic knowledge in one workspace—bringing key evidence together to support informed crop planning and farm decisions.</p>
     <div class="agri-tags"><span>🌱 Crop health &amp; planning</span><span>🌦️ Weather &amp; climate</span><span>🧪 Soil &amp; spatial evidence</span></div>
   </div>
   <div class="agri-hero-art" aria-hidden="true">
     <div class="agri-sun"></div><div class="agri-field field-back"></div><div class="agri-field field-mid"></div><div class="agri-field field-front"></div>
     <div class="agri-stalk stalk-one">🌾</div><div class="agri-stalk stalk-two">🌿</div><div class="agri-stalk stalk-three">🌱</div>
   </div>
 </section>
 <div class="agri-section-intro"><div><div class="agri-kicker">YOUR FARM INTELLIGENCE WORKSPACE</div><h2>One platform. Multiple perspectives.</h2></div><p>Explore the signals that shape agricultural productivity.</p></div>
 <div class="agri-feature-grid">
   <div class="agri-feature"><div class="agri-feature-icon">🌿</div><div><b>Crop health</b><small>Screen symptoms and explore practical next steps.</small></div></div>
   <div class="agri-feature"><div class="agri-feature-icon">🌦️</div><div><b>Weather & climate</b><small>Understand local forecasts and historical conditions.</small></div></div>
   <div class="agri-feature"><div class="agri-feature-icon">🌱</div><div><b>Crop planning</b><small>Build evidence-led crop and farm profiles.</small></div></div>
   <div class="agri-feature"><div class="agri-feature-icon">🗺️</div><div><b>Spatial evidence</b><small>Explore mapped observations and farm boundaries.</small></div></div>
   <div class="agri-feature"><div class="agri-feature-icon">🧪</div><div><b>Soil health</b><small>Interpret soil indicators and laboratory results.</small></div></div>
   <div class="agri-feature"><div class="agri-feature-icon">📚</div><div><b>Plant knowledge</b><small>Find general plant-care and species references.</small></div></div>
 </div>
 """, unsafe_allow_html=True)
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
 st.markdown('<div class="hero"><div class="module-eyebrow">CROP HEALTH & FIELD OBSERVATION</div><h1>🩺 Crop Health Screening</h1><p>Screen observed symptoms and receive cautious next steps.</p></div>',unsafe_allow_html=True)
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
 st.markdown('<div class="hero"><div class="module-eyebrow">CLIMATE & WEATHER INTELLIGENCE</div><h1>🌦️ Weather & Climate</h1><p>Forecast and historical climate indicators from free data services.</p></div>',unsafe_allow_html=True)
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
 st.markdown('<div class="hero"><div class="module-eyebrow">CROP & FARM PLANNING</div><h1>🌾 Crop Planning</h1><p>Build a crop-specific planning record using the actual farm location and cultivar.</p></div>',unsafe_allow_html=True)
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
 mapped_spatial = None
 valid_boundary = None
 boundary_bounds = None
 st.markdown('<div class="hero"><div class="module-eyebrow">GEOSPATIAL AGRICULTURAL EVIDENCE</div><h1>🗺️ Spatial Evidence Explorer</h1><p>Map farm or field observations and compare them with selected species-level ecological reference ranges.</p></div>',unsafe_allow_html=True)
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
      st_folium(spatial_map, height=520, width=1200, key='spatial_evidence_map')
      st.caption('Map markers show supplied observation coordinates only. Marker color does not indicate suitability, risk or crop performance.')
      st.download_button('Download validated spatial observations (CSV)', data=mapped_spatial.to_csv(index=False).encode('utf-8-sig'), file_name='agrinova_validated_spatial_observations.csv', mime='text/csv', key='spatial_observations_download')
    else:
     st.info('Select valid latitude and longitude columns to validate and map records.')
  except (ValueError, OSError, ImportError, UnicodeDecodeError, pd.errors.ParserError) as error:
   st.error(f'Could not read the uploaded geospatial file: {error}. Check the CSV or Excel format.')
 st.divider()
 st.markdown('**Farm and field boundary upload (GeoJSON)**')
 st.caption('Upload a GeoJSON polygon or multipolygon to outline a farm or field. Coordinates are validated and displayed; no area, ownership or suitability is inferred.')
 boundary_file = st.file_uploader('Upload farm boundary (.geojson or .json)', type=['geojson','json'], key='spatial_boundary_file')
 if boundary_file is not None:
  try:
   boundary_file.seek(0)
   boundary_data = json.load(boundary_file)
   valid_boundary, boundary_warnings, boundary_bounds = validate_geojson_boundaries(boundary_data)
   for warning in boundary_warnings:
    st.warning(warning)
   if valid_boundary is not None:
    boundary_count = len(valid_boundary['features'])
    st.success(f'Validated {boundary_count:,} polygon feature(s).')
    boundary_map = folium.Map(
     location=[
      (boundary_bounds[0][0] + boundary_bounds[1][0]) / 2,
      (boundary_bounds[0][1] + boundary_bounds[1][1]) / 2,
     ],
     zoom_start=12,
     control_scale=True,
    )
    folium.GeoJson(
     valid_boundary,
     name='Uploaded farm boundaries',
     style_function=lambda feature: {
      'color': '#16845B',
      'weight': 3,
      'fillColor': '#53C58B',
      'fillOpacity': 0.18,
     },
     tooltip=folium.GeoJsonTooltip(
      fields=list(valid_boundary['features'][0].get('properties', {}).keys())[:5]
     ) if valid_boundary['features'][0].get('properties') else None,
    ).add_to(boundary_map)
    boundary_map.fit_bounds(boundary_bounds)
    if mapped_spatial is not None and not mapped_spatial.empty:
     observation_layer = folium.FeatureGroup(name='Uploaded observation points', show=True)
     for _, point in mapped_spatial.iterrows():
      popup_text = (
       f"Source row: {int(point['source_row'])}<br>"
       f"Latitude: {point['latitude']:.5f}<br>"
       f"Longitude: {point['longitude']:.5f}"
      )
      folium.CircleMarker(
       location=[point['latitude'], point['longitude']],
       radius=5,
       color='#1976A8',
       fill=True,
       fill_color='#1976A8',
       fill_opacity=0.85,
       tooltip=f"Observation row {int(point['source_row'])}",
       popup=folium.Popup(popup_text, max_width=280),
      ).add_to(observation_layer)
     observation_layer.add_to(boundary_map)
    folium.LayerControl(collapsed=False).add_to(boundary_map)
    st.subheader('Uploaded farm boundary map')
    st_folium(boundary_map, height=520, width=1200, key='spatial_boundary_map')
    st.download_button(
     'Download validated GeoJSON',
     data=json.dumps(valid_boundary, ensure_ascii=False, indent=2).encode('utf-8'),
     file_name='agrinova_validated_farm_boundaries.geojson',
     mime='application/geo+json',
     key='spatial_boundary_download',
    )
    st.caption('Boundary geometry is shown as supplied after basic structural and coordinate checks. Complex polygon topology is not repaired or independently verified.')
  except (ValueError, OSError, UnicodeDecodeError) as error:
   st.error(f'Could not read the GeoJSON boundary file: {error}. Check that it is valid UTF-8 GeoJSON.')
 st.divider()
 st.markdown('**SoilGrids WCS coverage discovery (nitrogen)**')
 st.caption('Check the official ISRIC Web Coverage Service metadata and inspect the coverage identifiers currently advertised for the nitrogen layer. This reads service metadata only; no raster pixels or farm measurements are downloaded.')
 if st.button('Check live SoilGrids WCS coverages', key='check_soilgrids_wcs'):
  try:
   with st.spinner('Requesting official ISRIC WCS capabilities...'):
    st.session_state['soilgrids_wcs_coverages'] = fetch_nitrogen_coverages()
    st.session_state['soilgrids_wcs_error'] = None
  except Exception as error:
   st.session_state['soilgrids_wcs_coverages'] = None
   st.session_state['soilgrids_wcs_error'] = str(error)
 if st.session_state.get('soilgrids_wcs_coverages'):
  coverage_ids = st.session_state['soilgrids_wcs_coverages']
  st.success(f'ISRIC advertised {len(coverage_ids)} coverage identifier(s) in the latest successful check.')
  st.dataframe(pd.DataFrame({'WCS coverage identifier': coverage_ids}), use_container_width=True, hide_index=True)
  st.caption('Coverage identifiers are service metadata, not soil values. Each coverage represents a modeled nitrogen layer; depth interval and quantile are encoded in the identifier.')
 elif st.session_state.get('soilgrids_wcs_error'):
  st.warning(f"Live WCS metadata could not be retrieved: {st.session_state['soilgrids_wcs_error']}. The service may be temporarily unavailable; use the official documentation and map links below.")
 else:
  st.info('Run the check to retrieve current coverage metadata from ISRIC. Availability is not assumed.')
 if st.session_state.get('soilgrids_wcs_coverages'):
  available_nitrogen = [item for item in st.session_state['soilgrids_wcs_coverages'] if item.startswith('nitrogen_')]
  if available_nitrogen:
   selected_coverage = st.selectbox('Select nitrogen coverage', available_nitrogen, key='soilgrids_nitrogen_coverage')
   st.caption('Choose a depth interval and prediction layer. Median, mean and uncertainty layers are distinct modeled outputs.')
   if valid_boundary is not None and boundary_bounds is not None:
    st.caption('The request uses the bounding rectangle of the uploaded GeoJSON boundary, not an exact polygon clip. Keep the boundary extent small; the interactive limit is 0.25° in each direction.')
    if st.button('Request SoilGrids GeoTIFF for this boundary extent', key='request_soilgrids_geotiff'):
     try:
      with st.spinner('Requesting a bounded GeoTIFF subset from ISRIC...'):
       raster_bytes = fetch_nitrogen_geotiff(selected_coverage, boundary_bounds)
       st.session_state['soilgrids_geotiff_bytes'] = raster_bytes
       st.session_state['soilgrids_geotiff_name'] = selected_coverage.replace('.', '_') + '.tif'
       st.session_state['soilgrids_geotiff_coverage'] = selected_coverage
       st.session_state['soilgrids_geotiff_bounds'] = boundary_bounds
       st.session_state['soilgrids_geotiff_boundary'] = json.dumps(valid_boundary, sort_keys=True)
       st.session_state['soilgrids_analysis'] = None
       st.session_state['soilgrids_geotiff_error'] = None
     except Exception as error:
      st.session_state['soilgrids_geotiff_bytes'] = None
      st.session_state['soilgrids_geotiff_error'] = str(error)
    if (st.session_state.get('soilgrids_geotiff_bytes')
        and st.session_state.get('soilgrids_geotiff_coverage') == selected_coverage
        and st.session_state.get('soilgrids_geotiff_bounds') == boundary_bounds):
     st.success(f"GeoTIFF received ({len(st.session_state['soilgrids_geotiff_bytes']):,} bytes).")
     st.download_button(
      'Download SoilGrids nitrogen bounding-rectangle GeoTIFF',
      data=st.session_state['soilgrids_geotiff_bytes'],
      file_name=st.session_state['soilgrids_geotiff_name'],
      mime='image/tiff',
      key='soilgrids_geotiff_download',
     )
     boundary_fingerprint = json.dumps(valid_boundary, sort_keys=True)
     if st.button('Clip to exact farm polygon and calculate statistics', key='analyze_soilgrids_polygon'):
      try:
       with st.spinner('Clipping raster to the farm polygon and summarizing valid pixels...'):
        result = analyze_nitrogen_geotiff(
         st.session_state['soilgrids_geotiff_bytes'],
         valid_boundary,
        )
        st.session_state['soilgrids_analysis'] = result
        st.session_state['soilgrids_analysis_coverage'] = selected_coverage
        st.session_state['soilgrids_analysis_boundary'] = boundary_fingerprint
        st.session_state['soilgrids_analysis_error'] = None
      except Exception as error:
       st.session_state['soilgrids_analysis'] = None
       st.session_state['soilgrids_analysis_error'] = str(error)
     analysis = st.session_state.get('soilgrids_analysis')
     if (analysis
         and st.session_state.get('soilgrids_analysis_coverage') == selected_coverage
         and st.session_state.get('soilgrids_analysis_boundary') == boundary_fingerprint):
      st.subheader('Farm polygon nitrogen raster summary')
      st.caption('Descriptive statistics for valid modeled SoilGrids pixels inside the uploaded polygon. Source layer units: cg/kg. These are not laboratory measurements.')
      m1, m2, m3 = st.columns(3)
      with m1: metric('Mean nitrogen', f"{analysis['mean_cg_kg']:.2f} cg/kg", 'Modeled pixel average')
      with m2: metric('Median nitrogen', f"{analysis['median_cg_kg']:.2f} cg/kg", 'Modeled pixel median')
      with m3: metric('Valid pixel coverage', f"{analysis['valid_coverage_pct']:.1f}%", f"{analysis['valid_pixel_count']:,} of {analysis['pixel_count_inside_polygon']:,} polygon pixels")
      stats = pd.DataFrame([
       {'Statistic': 'Minimum', 'Value': analysis['minimum_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': '25th percentile', 'Value': analysis['q25_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': 'Mean', 'Value': analysis['mean_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': 'Median', 'Value': analysis['median_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': '75th percentile', 'Value': analysis['q75_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': 'Maximum', 'Value': analysis['maximum_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': 'Standard deviation', 'Value': analysis['std_cg_kg'], 'Unit': 'cg/kg'},
       {'Statistic': 'NoData pixels', 'Value': analysis['nodata_pixel_count'], 'Unit': 'pixels'},
      ])
      st.dataframe(stats, use_container_width=True, hide_index=True)
      st.caption(f"Raster CRS: {analysis['raster_crs']} · Pixel size: {analysis['raster_resolution']} · Pixel inclusion: {'all touched' if analysis['all_touched'] else 'pixel centre'}")
      st.download_button(
       'Download exact-polygon-clipped nitrogen GeoTIFF',
       data=analysis['clipped_geotiff'],
       file_name=selected_coverage.replace('.', '_') + '_farm_polygon_clip.tif',
       mime='image/tiff',
       key='soilgrids_polygon_clip_download',
      )
     elif st.session_state.get('soilgrids_analysis_error'):
      st.warning(f"Raster analysis failed: {st.session_state['soilgrids_analysis_error']}")
    elif st.session_state.get('soilgrids_geotiff_error'):
     st.warning(f"GeoTIFF request failed: {st.session_state['soilgrids_geotiff_error']}")
   else:
    st.info('Upload and validate a GeoJSON farm boundary before requesting a raster subset.')
 st.markdown(f"[Open official SoilGrids WCS documentation]({SOILGRIDS_WCS_DOCS}) · [Open nitrogen WCS endpoint]({SOILGRIDS_NITROGEN_WCS})")
 st.caption("The SoilGrids REST point-query API remains separate from WCS. The integration downloads a bounded nitrogen GeoTIFF, clips it to the exact uploaded polygon, and calculates descriptive statistics from valid modeled pixels. Results retain the source layer's cg/kg units and are not laboratory measurements.")
 st.markdown('**Preparing source data**')
 st.markdown('- Export point or sample data from your GIS workflow with latitude and longitude columns.\n- GAEZ and SoilGrids downloads may be gridded raster data; convert or sample them using a GIS tool before uploading point observations.\n- Keep source names, units, depth, dates, spatial resolution and reference period with the dataset.\n- Do not combine measurements from different soil depths or incompatible laboratory methods as if they were equivalent.')
 st.caption('Spatial workflow: CSV / Excel point observations and GeoJSON Polygon / MultiPolygon boundaries are supported. When both are supplied, the boundary map can display them as separate layers. A bounded nitrogen GeoTIFF can be downloaded, clipped to the exact uploaded GeoJSON polygon and summarized with valid-pixel counts, coverage percentage, mean, median, quartiles, minimum, maximum and standard deviation. Other SoilGrids properties are not yet implemented.')
elif page=='Soil Health':
 st.markdown('<div class="hero"><div class="module-eyebrow">SOIL SCIENCE & FIELD MEASUREMENTS</div><h1>🧪 Soil Health</h1><p>Explore global modeled soil information and interpret your own laboratory measurements.</p></div>',unsafe_allow_html=True)
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
 st.markdown('<div class="hero"><div class="module-eyebrow">AGRONOMY & PLANT KNOWLEDGE</div><h1>📚 Agricultural Knowledge Assistant</h1><p>Ask about any plant, from vegetables and fruit trees to herbs and ornamentals. Search broad plant-care references and available crop-specific guidance locally; no external AI service or paid API key is required.</p></div>',unsafe_allow_html=True)
 q=st.text_input('Ask an agricultural question', placeholder='e.g. eggplant care, dragon fruit watering, mango tree pests, sorghum, soil organic matter')
 category=st.selectbox('Topic',['All']+sorted({x['category'] for x in KNOWLEDGE}), key='knowledge_topic_filter')
 search_col, clear_col = st.columns([1, 1])
 with search_col:
  search_clicked = st.button('Search knowledge library', use_container_width=True, key='knowledge_search_button')
 with clear_col:
  clear_clicked = st.button('Clear search', use_container_width=True, key='knowledge_clear_button')
 if search_clicked:
  st.session_state['knowledge_search_query'] = q.strip()
  st.session_state['knowledge_search_category'] = category
  st.session_state['knowledge_search_results'] = search_knowledge(q, category) if q.strip() else []
  st.session_state['knowledge_ecocrop_matches'] = search_ecocrop(q) if q.strip() else []
  st.session_state['knowledge_search_submitted'] = True
 if clear_clicked:
  for key in ('knowledge_search_query','knowledge_search_category','knowledge_search_results','knowledge_ecocrop_matches','knowledge_search_submitted'):
   st.session_state.pop(key, None)
 if st.session_state.get('knowledge_search_submitted'):
  submitted_query = st.session_state.get('knowledge_search_query', '')
  submitted_category = st.session_state.get('knowledge_search_category', 'All')
  if not submitted_query:
   st.info('Enter a question or a few keywords before searching.')
  elif submitted_category != category:
   st.info('The topic filter has changed. Run the search again to refresh the results.')
  else:
   eco_matches = st.session_state.get('knowledge_ecocrop_matches', [])
   if eco_matches:
    st.markdown('**Species-level reference (FAO ECOCROP)**')
    eco_options = {record['_display']: record for record in eco_matches}
    selected_eco_label = st.selectbox('Confirm the plant species', list(eco_options), key='knowledge_ecocrop_species')
    eco = eco_options[selected_eco_label]
    def _knowledge_eco_value(value, unit=''):
     if value is None or (isinstance(value, float) and pd.isna(value)):
      return 'Not available'
     if isinstance(value, (int, float)):
      return f'{value:g}{unit}'
     if isinstance(value, (list, tuple)):
      return ', '.join(str(x) for x in value)
     return str(value)
    def _knowledge_eco_range(low, high, unit=''):
     left = _knowledge_eco_value(eco.get(low), unit)
     right = _knowledge_eco_value(eco.get(high), unit)
     return f'{left} to {right}' if left != 'Not available' or right != 'Not available' else 'Not available'
    eco_rows = [
     {'Ecological indicator':'Optimal temperature range','ECOCROP reference':_knowledge_eco_range('topmn','topmx',' °C')},
     {'Ecological indicator':'Absolute temperature limits','ECOCROP reference':_knowledge_eco_range('tmin','tmax',' °C')},
     {'Ecological indicator':'Optimal annual rainfall','ECOCROP reference':_knowledge_eco_range('ropmn','ropmx',' mm/year')},
     {'Ecological indicator':'Absolute annual rainfall limits','ECOCROP reference':_knowledge_eco_range('rmin','rmax',' mm/year')},
     {'Ecological indicator':'Crop-cycle range','ECOCROP reference':_knowledge_eco_range('gmin','gmax',' days')},
     {'Ecological indicator':'Optimal soil pH','ECOCROP reference':_knowledge_eco_range('phopmn','phopmx')},
     {'Ecological indicator':'Absolute soil pH limits','ECOCROP reference':_knowledge_eco_range('phmin','phmax')},
     {'Ecological indicator':'Preferred soil texture','ECOCROP reference':_knowledge_eco_value(eco.get('text'))},
     {'Ecological indicator':'Climate zones','ECOCROP reference':_knowledge_eco_value(eco.get('cliz'))},
    ]
    st.success(f"Species record: {eco.get('scientificname', 'Scientific name not listed')}")
    st.dataframe(pd.DataFrame(eco_rows), use_container_width=True, hide_index=True)
    eco_id = eco.get('ecoportcode', '')
    if eco_id:
     st.caption(f"ECOCROP record ID: {eco_id} · [Open FAO ECOCROP species record](https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id={eco_id})")
    st.caption('Source: FAO ECOCROP species reference, distributed through the CGIAR Climate Action Data Hub. These are expert-compiled ecological references, not farm measurements or cultivar-specific prescriptions. Missing values remain unavailable.')
   else:
    st.info('No matching species record was returned by ECOCROP for this query. General plant-care references may still be useful; the absence of a match does not mean the plant is unsupported by agriculture.')
   results = st.session_state.get('knowledge_search_results', [])
   st.subheader('General knowledge references')
   if results:
    st.caption(f"{len(results)} general reference(s) related to: {submitted_query}. These are not species-specific unless explicitly stated.")
    for item in results:
     with st.expander(item['title'], expanded=True):
      st.write(item['answer'])
      st.caption('Topic: '+item['category']+' · Source: '+item['source'])
   else:
    st.info('No close general reference was found. Try describing the growing condition or symptom, or browse the general plant-care library below.')
 st.subheader('Knowledge library')
 visible_items = [item for item in KNOWLEDGE if category=='All' or item['category']==category]
 st.caption(f'{len(visible_items)} curated entries available')
 for item in visible_items:
  with st.expander(item['title']):
   st.write(item['answer'])
   st.caption('Topic: '+item['category']+' · Source: '+item['source'])
elif page=='Data Sources & Methodology':
 st.markdown('<div class="hero"><div class="module-eyebrow">DATA TRANSPARENCY & METHODS</div><h1>🗂️ Data Sources & Methodology</h1><p>Transparent source coverage, access notes and limitations.</p></div>',unsafe_allow_html=True)
 st.dataframe(pd.DataFrame(DATA_SOURCES),use_container_width=True,hide_index=True,column_config={'URL':st.column_config.LinkColumn('Source website')})
 st.subheader('Interpretation rules')
 st.markdown('- Prefer Somalia-specific observed data when available.\n- Clearly label regional estimates and global modeled information.\n- Satellite observations are not ground observations.\n- Soil maps do not replace farm-level laboratory tests.\n- Check licenses and terms before commercial reuse.')
 st.info('Included functions use public/free access services where possible. Some source portals may require free registration or have product-specific terms.')
st.divider(); st.caption('AgriNova AI • Agricultural Intelligence Platform • Python + Streamlit • Free-data-first')
