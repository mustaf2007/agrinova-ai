import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data_sources import get_weather, get_historical_climate, search_global_locations, DATA_SOURCES
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

def global_location_picker(key, label="Search location worldwide"):
 query = st.text_input(label, placeholder="Enter a city, region or country (e.g. Nairobi, Punjab, Brazil)", key=f"{key}_global_search")
 if len(query.strip()) < 2:
  st.caption("Global coverage is selected by default. Search any location to load local weather and climate information.")
  return None
 matches = search_global_locations(query)
 if not matches:
  st.info("No matching locations found. Try a nearby city, a different spelling or a country name.")
  return None
 options = {item["label"]: item for item in matches}
 selected_label = st.selectbox("Matching locations", list(options), key=f"{key}_global_match")
 return options[selected_label]
with st.sidebar:
 st.markdown('## 🌱 AgriNova AI'); st.caption('Agricultural Intelligence Platform'); st.divider()
 page=st.radio('WORKSPACE',['Overview','Crop Health Screening','Weather & Climate','Crop Planner','Soil Health','Agri Knowledge Assistant','Data Sources & Methodology'])
 st.divider(); theme=st.selectbox('Appearance theme',list(THEMES),index=list(THEMES).index(st.session_state.theme))
 if theme!=st.session_state.theme: st.session_state.theme=theme; st.rerun()
 st.caption('Free-data-first • No paid API keys')
if page=='Overview':
 st.markdown('<div class="hero"><h1>🌱 AgriNova AI</h1><p>AI-powered agricultural intelligence for healthier crops and better farming decisions.</p></div>',unsafe_allow_html=True)
 location = global_location_picker("overview")
 crop=st.selectbox('Crop focus',list(CROPS))
 w = get_weather(location["latitude"], location["longitude"]) if location else None
 x1,x2,x3,x4=st.columns(4)
 with x1: metric('Geographic coverage','Worldwide','Search any country, region or city')
 with x2: metric('Crop focus',crop,'Planning selection')
 with x3: metric('Temperature',f"{w['current_temp']} °C" if w and w.get('current_temp') is not None else 'Select location','Open-Meteo forecast')
 with x4: metric('7-day rainfall',f"{w['rain_7d']} mm" if w else 'Select location','Forecast total')
 st.subheader('Weather outlook')
 if w and w['daily']:
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
  with a: crop=st.selectbox('Crop',list(CROPS)); part=st.selectbox('Affected part',['Leaves','Stem','Roots','Fruit / grain','Whole plant']); symptoms=st.multiselect('Symptoms',['Yellowing leaves','Brown or black spots','White powdery growth','Wilting','Holes or chewing damage','Mosaic / mottled pattern','Stunted growth','Rotting / soft tissue','Rust-colored pustules','Leaf edges drying'])
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
  a,b,c,d=st.columns(4)
  with a: metric('Temperature',f"{w['current_temp']} °C")
  with b: metric('Humidity',f"{w['humidity']}%")
  with c: metric('Wind',f"{w['wind']} km/h")
  with d: metric('7-day rain',f"{w['rain_7d']} mm")
  df=pd.DataFrame(w['daily']); st.plotly_chart(px.line(df,x='date',y=['temp_max','temp_min'],markers=True),use_container_width=True); st.plotly_chart(px.bar(df,x='date',y='precipitation'),use_container_width=True)
  st.subheader('NASA POWER historical climate'); hist=get_historical_climate(lat,lon)
  if hist is not None and not hist.empty: st.line_chart(hist.set_index('date')[['T2M','PRECTOTCORR']]); st.dataframe(hist.tail(30),use_container_width=True)
  else: st.info('Historical data not currently returned by NASA POWER.')
 else: st.info('Worldwide mode is active. Search a city, region or country above to load its forecast. If you already selected a location, check internet connectivity.')
elif page=='Crop Planner':
 st.markdown('<div class="hero"><h1>🌾 Crop Planning</h1><p>Crop-specific general guidance and planning considerations.</p></div>',unsafe_allow_html=True)
 region = global_location_picker("planner", "Search farm location worldwide (optional)")
 a,b=st.columns(2)
 with a: crop=st.selectbox('Crop',list(CROPS))
 with b: area=st.number_input('Farm size (hectares)',min_value=.01,value=1.0,step=.5); season=st.selectbox('Season',['Main rainy season','Short rainy season','Dry / irrigated season','Not sure'])
 region_name = region["label"] if region else "Global / location not specified"
 g=get_crop_guidance(crop,region_name,season,area); a,b,c=st.columns(3)
 with a: metric('Crop',crop)
 with b: metric('Water demand',g['water'])
 with c: metric('Growing duration',g['duration'])
 st.subheader('Practical guidance')
 for item in g['guidance']: st.markdown('- '+item)
 st.subheader('Planning considerations')
 for item in g['cautions']: st.markdown('- '+item)
elif page=='Soil Health':
 st.markdown('<div class="hero"><h1>🧪 Soil Health</h1><p>Interpret soil measurements supplied by the user.</p></div>',unsafe_allow_html=True)
 st.info('Use laboratory or field-test results. The app does not invent missing measurements or fertilizer rates.')
 with st.form('soil'):
  a,b,c=st.columns(3)
  with a: ph=st.number_input('Soil pH',0.,14.,6.5,.1); organic=st.number_input('Organic matter (%)',0.,100.,1.5,.1)
  with b: ec=st.number_input('Electrical conductivity (dS/m)',0.,100.,.5,.1); n=st.number_input('Nitrogen (mg/kg)',0.,value=20.)
  with c: p=st.number_input('Available phosphorus (mg/kg)',0.,value=10.); k=st.number_input('Available potassium (mg/kg)',0.,value=100.)
  crop=st.selectbox('Crop',list(CROPS)); submit=st.form_submit_button('Assess soil indicators')
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
