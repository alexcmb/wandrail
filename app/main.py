import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster, LocateControl
from streamlit_folium import st_folium
from sqlalchemy import create_engine, text
import numpy as np
import hashlib, secrets, requests, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Wandrail", page_icon="images/logo.png" if os.path.exists("images/logo.png") else None,
                   layout="wide", initial_sidebar_state="expanded")

for k, v in {
    "dark_mode": False, "page": "accueil", "dest_sel": None,
    "profil_sel": None, "planner_step": 1, "user": None, "search_q": "",
    "show_auth": False,
    "f_dep": [], "f_prof": [], "f_traveler": [], "f_score": 0.0, "f_type": None,
    "f_sort": "Score", "f_nb": 24,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

dk = st.session_state.dark_mode

if dk:
    BG="#080e1c"; CARD="#0f1a2e"; CARD2="#111f34"; BORDER="rgba(255,255,255,0.08)"
    BORDER2="rgba(255,255,255,0.15)"; TEXT="#f0f4ff"; TEXT2="#8a9fc0"
    SHADOW="0 8px 40px rgba(0,0,0,.7)"; SHADOW2="0 2px 14px rgba(0,0,0,.5)"
    SBARBG="#060c18"; INPUT="#1a2540"; NAVBG="rgba(8,14,28,0.97)"
    HERO_OV="linear-gradient(165deg,rgba(4,8,24,0.9),rgba(10,40,90,0.6))"
    BADGE_BG="rgba(255,255,255,0.1)"; ECO_BG="linear-gradient(135deg,#022c17,#064e3b)"
    ECO_NUM="#34d399"; ECO_LBL="#6ee7b7"; TILE="CartoDB dark_matter"
    CHART_BG="#0f1a2e"; CO2GB="#10b981"; CO2BB="#ef4444"
    TAGBG="rgba(59,130,246,0.15)"; TAGC="#7dbff5"; FOOT="#04070f"
else:
    BG="#ffffff"; CARD="#ffffff"; CARD2="#f5f5f5"; BORDER="rgba(0,0,0,0.09)"
    BORDER2="rgba(0,0,0,0.18)"; TEXT="#111111"; TEXT2="#6b6b6b"
    SHADOW="0 8px 32px rgba(0,0,0,.12)"; SHADOW2="0 2px 12px rgba(0,0,0,.07)"
    SBARBG="#ffffff"; INPUT="#f5f5f5"; NAVBG="rgba(255,255,255,0.98)"
    HERO_OV="linear-gradient(165deg,rgba(10,40,100,0.88),rgba(30,100,180,0.55))"
    BADGE_BG="rgba(0,0,0,0.45)"; ECO_BG="linear-gradient(135deg,#d1fae5,#a7f3d0)"
    ECO_NUM="#065f46"; ECO_LBL="#047857"; TILE="CartoDB positron"
    CHART_BG="#ffffff"; CO2GB="#16a34a"; CO2BB="#dc2626"
    TAGBG="rgba(124,58,237,0.08)"; TAGC="#5b21b6"; FOOT="#111111"

BLUE="#8b5cf6" if dk else "#7c3aed"
BLDARK="#6d28d9" if dk else "#4c1d95"
GREEN="#22c55e" if dk else "#16a34a"
ACCENT="#f97316"
SNCF="#e2001a"
CORAL="#ff385c"

# ── CSS ────────────────────────────────────────────────────────
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');
@keyframes pageIn {{
  from {{opacity:0;transform:translateY(22px)}}
  to {{opacity:1;transform:translateY(0)}}
}}
@keyframes fadeUp {{
  from {{opacity:0;transform:translateY(12px)}}
  to {{opacity:1;transform:translateY(0)}}
}}
@keyframes heroPulse {{
  0%,100% {{transform:scale(1);opacity:.22}}
  50% {{transform:scale(1.08);opacity:.32}}
}}

*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body,[class*="css"]{{font-family:'Space Grotesk','Plus Jakarta Sans',sans-serif!important}}
[data-testid="stSidebar"]{{background:{SBARBG}!important;border-right:1px solid {BORDER}!important;padding-top:0!important}}
[data-testid="stHeader"]{{display:none!important}}
.main .block-container{{padding:0!important;max-width:100%!important}}
body,.main,[data-testid="stAppViewContainer"]{{background:{BG}!important}}
[data-testid="stVerticalBlock"]{{gap:0!important}}

/* PAGE TRANSITION */
.main .block-container > div {{animation:pageIn 0.48s cubic-bezier(0.22,1,0.36,1)}}

.stTextInput>div>div>input{{background:{INPUT}!important;border:1.5px solid {BORDER2}!important;
  color:{TEXT}!important;border-radius:10px!important;padding:10px 14px!important;font-size:.9rem!important}}
.stTextInput>div>div>input:focus{{border-color:{BLUE}!important;box-shadow:0 0 0 3px {BLUE}25!important}}
.stTextInput label,.stSelectbox label,.stTextArea label,.stSlider label{{color:{TEXT2}!important;font-size:.78rem!important;font-weight:500!important}}
.stSelectbox>div>div{{background:{INPUT}!important;border:1.5px solid {BORDER2}!important;color:{TEXT}!important;border-radius:10px!important}}
.stTextArea textarea{{background:{INPUT}!important;border:1.5px solid {BORDER2}!important;color:{TEXT}!important;border-radius:10px!important}}
.stSlider>div>div>div>div{{background:{BLUE}!important}}
.stCheckbox span{{color:{TEXT}!important;font-size:.85rem!important}}
[data-testid="stVerticalBlock"]>div:has(.dcard)+div [data-testid="stHorizontalBlock"]{{margin-top:-6px!important}}
.stButton>button{{border-radius:9px!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:600!important;
  font-size:.84rem!important;transition:all .16s!important;border:1.5px solid {BORDER2}!important;
  background:{CARD}!important;color:{TEXT}!important;padding:9px 16px!important}}
.stButton>button:hover{{border-color:{BLUE}!important;color:{BLUE}!important;background:{TAGBG}!important}}
.stButton>button[kind="primary"]{{background:{BLUE}!important;color:#fff!important;border-color:{BLUE}!important}}
.stButton>button[kind="primary"]:hover{{background:{BLDARK}!important;border-color:{BLDARK}!important;box-shadow:0 3px 12px {BLUE}40!important}}
.stTabs [data-baseweb="tab-list"]{{background:{CARD2}!important;border-radius:12px!important;padding:3px!important;gap:3px!important;border:1px solid {BORDER}!important}}
.stTabs [data-baseweb="tab"]{{border-radius:9px!important;color:{TEXT2}!important;font-weight:600!important;font-size:.83rem!important;padding:9px 18px!important;background:transparent!important;}}
.stTabs [aria-selected="true"]{{background:{BLUE}!important;color:#fff!important}}
.stTabs [data-baseweb="tab-panel"]{{padding:0!important}}
.stSpinner>div{{border-top-color:{BLUE}!important}}

/* NAVBAR — style SNCF Connect */
.tvnav{{position:sticky;top:0;z-index:999;background:{NAVBG};backdrop-filter:blur(20px);
  border-bottom:1px solid {BORDER};padding:0 2.2rem;display:flex;align-items:center;
  justify-content:space-between;height:58px;box-shadow:0 2px 12px rgba(0,0,0,.06)}}
.tv-brand{{display:flex;align-items:center;gap:10px;font-size:1.08rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;text-decoration:none}}
.tv-brand-dot{{width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,{BLUE},{ACCENT});animation:heroPulse 3s ease-in-out infinite}}
.tv-nav{{display:flex;align-items:center;gap:0}}
.tv-nav-lnk{{padding:0 14px;height:58px;display:flex;align-items:center;font-size:.82rem;
  font-weight:600;color:{TEXT2};text-decoration:none;border-bottom:3px solid transparent;
  transition:all .18s;cursor:pointer;white-space:nowrap}}
.tv-nav-lnk:hover{{color:{BLUE};border-bottom-color:{BLUE}30}}
.tv-nav-lnk.cur{{color:{BLUE};border-bottom-color:{BLUE};font-weight:700}}
.tv-right{{display:flex;align-items:center;gap:10px}}

/* CATEGORY CHIPS — style Airbnb */
.cat-scroll{{display:flex;gap:.65rem;overflow-x:auto;padding:1.6rem 2.5rem 1rem;
  scrollbar-width:none;border-bottom:1px solid {BORDER}}}
.cat-scroll::-webkit-scrollbar{{display:none}}
.cat-chip{{display:inline-flex;align-items:center;padding:9px 22px;border-radius:24px;
  border:1.5px solid {BORDER2};background:{CARD};color:{TEXT2};font-size:.8rem;font-weight:600;
  cursor:pointer;white-space:nowrap;transition:all .18s;text-decoration:none;flex-shrink:0}}
.cat-chip:hover{{border-color:{BLUE};color:{BLUE}}}
.cat-chip.active{{border-color:{BLUE};color:#fff;background:{BLUE}}}

/* ACTIVITY CARD */
.acard{{border:1px solid {BORDER};border-radius:12px;overflow:hidden;background:{CARD};transition:all .2s}}
.acard:hover{{box-shadow:{SHADOW2};border-color:{BORDER2};transform:translateY(-2px)}}
.acard-img{{height:90px;position:relative;overflow:hidden;background:{CARD2}}}
.acard-img img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
.acard-ico{{position:absolute;bottom:4px;right:5px;background:rgba(0,0,0,.45);border-radius:4px;padding:2px 5px}}
.acard-body{{padding:.7rem .85rem .85rem}}
.acard-nm{{font-weight:700;font-size:.81rem;color:{TEXT};margin:0 0 4px;line-height:1.3}}
.acard-mt{{font-size:.68rem;color:{TEXT2};line-height:1.75;margin:0}}

/* TRAVELER TYPE BADGE */
.traveler-badge{{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:16px;
  font-size:.7rem;font-weight:600;margin-right:4px}}

/* SNCF CTA BUTTON */
.sncf-cta{{display:inline-flex;align-items:center;gap:8px;background:{SNCF};color:#fff;
  border-radius:12px;padding:12px 20px;font-size:.85rem;font-weight:700;text-decoration:none;
  transition:all .2s;border:none;box-shadow:0 4px 12px {SNCF}40;cursor:pointer}}
.sncf-cta:hover{{background:#b8001a;transform:translateY(-2px);box-shadow:0 6px 18px {SNCF}60}}

/* CO2 COMPARISON GRID */
.co2-compare{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:1rem 0}}
.co2-item{{border:2px solid;border-radius:12px;padding:1rem;text-align:center}}
.co2-item.train{{border-color:{CO2GB};background:{CO2GB}15}}
.co2-item.car{{border-color:{CO2BB};background:{CO2BB}15}}
.co2-num{{font-size:1.8rem;font-weight:900;margin-bottom:4px}}

/* MOBILITY SECTION */
.mobility-card{{border:1px solid {BORDER};border-radius:12px;padding:1rem;background:{CARD};margin-bottom:.8rem}}
.mobility-title{{font-weight:700;color:{TEXT};margin-bottom:6px}}
.mobility-desc{{font-size:.75rem;color:{TEXT2}}}

</style>""", unsafe_allow_html=True)

# ── DB ─────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    if "DATABASE_URL" in st.secrets:
        url = st.secrets["DATABASE_URL"]
    else:
        url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:00000@localhost:5434/tourisme_train"
        )
    return create_engine(url)

@st.cache_data(ttl=3600)
def load_dest():
    return pd.read_sql("""
        SELECT g.nom_gare, g.commune, g.departement, g.latitude, g.longitude,
               d.score_attractivite, d.profil_touristique, d.nb_poi_5km, d.nb_categories
        FROM silver.gares g LEFT JOIN gold.dim_gare d ON d.code_uic=g.code_uic
        WHERE g.latitude IS NOT NULL AND d.score_attractivite IS NOT NULL
        ORDER BY d.score_attractivite DESC
    """, get_engine())

@st.cache_data(ttl=3600)
def load_poi(nom_gare, rayon=10):
    return pd.read_sql(f"""
        SELECT p.nom, p.categorie, p.commune, p.latitude, p.longitude, p.note_moyenne,
               pe.distance_gare_km, pe.temps_marche_min
        FROM silver.poi p JOIN silver.poi_enrichi pe ON pe.id_poi=p.id
        WHERE pe.nom_gare='{nom_gare}' AND pe.distance_gare_km<={rayon}
          AND p.latitude IS NOT NULL ORDER BY pe.distance_gare_km LIMIT 300
    """, get_engine())

@st.cache_data(ttl=3600)
def load_reco(profil):
    return pd.read_sql(f"""
        SELECT r.rang, r.score_reco, r.raison, g.nom_gare, g.commune,
               g.score_attractivite, g.profil_touristique, g.nb_poi_5km
        FROM gold.recommandations r
        JOIN gold.dim_profil p ON p.id=r.id_profil
        JOIN gold.dim_gare g ON g.id=r.id_gare
        WHERE p.nom='{profil}' ORDER BY r.rang
    """, get_engine())

@st.cache_data(ttl=3600)
def load_poi_map():
    return pd.read_sql("""
        SELECT p.nom, p.categorie, p.latitude, p.longitude
        FROM silver.poi p JOIN silver.poi_enrichi pe ON pe.id_poi=p.id
        WHERE p.latitude IS NOT NULL ORDER BY RANDOM() LIMIT 4000
    """, get_engine())

def get_reviews(destination):
    try:
        return pd.read_sql(f"""
            SELECT u.pseudo, r.rating, r.comment, r.created_at
            FROM userapp.user_reviews r JOIN userapp.users u ON u.id=r.user_id
            WHERE r.destination='{destination}' ORDER BY r.created_at DESC
        """, get_engine())
    except: return pd.DataFrame()

def get_user_stats(user_id):
    try:
        visits = pd.read_sql(f"SELECT * FROM userapp.user_visits WHERE user_id={user_id}", get_engine())
        favs   = pd.read_sql(f"SELECT * FROM userapp.user_favorites WHERE user_id={user_id}", get_engine())
        revs   = pd.read_sql(f"SELECT * FROM userapp.user_reviews WHERE user_id={user_id}", get_engine())
        return visits, favs, revs
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def is_fav(user_id, dest):
    try:
        r = pd.read_sql(f"SELECT id FROM userapp.user_favorites WHERE user_id={user_id} AND destination='{dest}'", get_engine())
        return len(r) > 0
    except: return False

def toggle_fav(user_id, dest):
    eng = get_engine()
    with eng.begin() as conn:
        ex = conn.execute(text("SELECT id FROM userapp.user_favorites WHERE user_id=:u AND destination=:d"), {"u":user_id,"d":dest}).fetchone()
        if ex: conn.execute(text("DELETE FROM userapp.user_favorites WHERE user_id=:u AND destination=:d"), {"u":user_id,"d":dest})
        else:  conn.execute(text("INSERT INTO userapp.user_favorites(user_id,destination) VALUES(:u,:d)"), {"u":user_id,"d":dest})

def log_visit(user_id, dest, co2_kg, dist_km):
    eng = get_engine()
    with eng.begin() as conn:
        ex = conn.execute(text("SELECT id FROM userapp.user_visits WHERE user_id=:u AND destination=:d"), {"u":user_id,"d":dest}).fetchone()
        if not ex:
            conn.execute(text("INSERT INTO userapp.user_visits(user_id,destination,co2_saved_kg,dist_km) VALUES(:u,:d,:c,:km)"),
                        {"u":user_id,"d":dest,"c":co2_kg,"km":dist_km})

def add_review(user_id, dest, rating, comment):
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(text("""
            INSERT INTO userapp.user_reviews(user_id,destination,rating,comment)
            VALUES(:u,:d,:r,:c)
            ON CONFLICT(user_id,destination) DO UPDATE SET rating=:r,comment=:c
        """), {"u":user_id,"d":dest,"r":rating,"c":comment})

# ── Auth ────────────────────────────────────────────────────────
def hash_pw(pw):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 100000)
    return f"{salt}:{h.hex()}"

def verify_pw(pw, stored):
    try:
        salt, h = stored.split(':')
        h2 = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 100000)
        return h2.hex() == h
    except: return False

def login_user(email, pw):
    try:
        r = pd.read_sql(f"SELECT id,pseudo,email,password_hash,ville_depart FROM userapp.users WHERE email='{email}'", get_engine())
        if len(r) == 0: return None, "Email introuvable"
        row = r.iloc[0]
        if verify_pw(pw, row['password_hash']): return dict(row), None
        return None, "Mot de passe incorrect"
    except Exception as e: return None, str(e)

def register_user(email, pseudo, pw, ville):
    try:
        eng = get_engine()
        with eng.begin() as conn:
            conn.execute(text("INSERT INTO userapp.users(email,pseudo,password_hash,ville_depart) VALUES(:e,:p,:h,:v)"),
                        {"e":email,"p":pseudo,"h":hash_pw(pw),"v":ville})
        return True, None
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower(): return False, "Email déjà utilisé"
        return False, str(e)

# ── Weather ─────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def get_weather(commune):
    try:
        r = requests.get(f"https://wttr.in/{commune.replace(' ','+')},France?format=j1", timeout=5)
        d = r.json()
        c = d['current_condition'][0]
        fc = d.get('weather', [])
        code = str(c.get('weatherCode', '116'))
        ICONS = {
            "113":("fa-solid fa-sun","#f59e0b"), "116":("fa-solid fa-cloud-sun","#f59e0b"),
            "119":("fa-solid fa-cloud","#8a9fc0"), "122":("fa-solid fa-cloud","#64748b"),
            "176":("fa-solid fa-cloud-rain","#3b82f6"), "200":("fa-solid fa-bolt","#f59e0b"),
            "227":("fa-solid fa-snowflake","#7dd3fc"), "266":("fa-solid fa-cloud-drizzle","#60a5fa"),
            "302":("fa-solid fa-cloud-rain","#3b82f6"), "308":("fa-solid fa-cloud-showers-heavy","#1d4ed8"),
        }
        ico, col = ICONS.get(code, ("fa-solid fa-cloud-sun","#f59e0b"))
        days = []
        for day in fc[:3]:
            days.append({"date":day.get('date',''), "max":day.get('maxtempC','--'),
                         "min":day.get('mintempC','--'),
                         "desc":day['hourly'][4]['weatherDesc'][0]['value'] if day.get('hourly') else ""})
        return {"temp":c['temp_C'],"feels":c['FeelsLikeC'],"desc":c['weatherDesc'][0]['value'],
                "humidity":c['humidity'],"wind":c['windspeedKmph'],"icon":ico,"color":col,"days":days}
    except: return None

# ── Images ─────────────────────────────────────────────────────
def uimg(seed, w=800, h=500):
    clean = seed.replace(' ', '').replace(',', '').replace('+', '').replace("'", '')[:20]
    return f"https://picsum.photos/seed/{clean}/{w}/{h}"

def pimg(id_, w=800, h=500):
    return f"https://picsum.photos/id/{id_}/{w}/{h}"

HERO_IMG = "https://picsum.photos/id/1048/1920/900"

_FALLBACK_IDS = [175, 100, 103, 192, 181, 130, 116, 169, 76, 74, 583, 248, 379, 431, 592, 826]

def _fimg(nom):
    idx = sum(ord(c) for c in str(nom)) % len(_FALLBACK_IDS)
    return pimg(_FALLBACK_IDS[idx])

DEST_META = {
    "saumur":            {"img": pimg(40),  "grad": "linear-gradient(135deg,#0f2a5c,#1e4c9e)",
                          "tags":["Château","Vin d'Anjou","Loire"],"icon":"fa-solid fa-chess-rook","color":"#60a5fa"},
    "le mans":           {"img": pimg(175), "grad": "linear-gradient(135deg,#1a1a1a,#3d3d3d)",
                          "tags":["Circuit 24H","Cathédrale","Sport"],"icon":"fa-solid fa-flag-checkered","color":"#fca5a5"},
    "angers-st-laud":    {"img": pimg(192), "grad": "linear-gradient(135deg,#3d1f06,#7a3d0d)",
                          "tags":["Château","Tapisserie","Maine"],"icon":"fa-solid fa-landmark","color":"#fcd34d"},
    "angers":            {"img": pimg(192), "grad": "linear-gradient(135deg,#3d1f06,#7a3d0d)",
                          "tags":["Château","Tapisserie","Maine"],"icon":"fa-solid fa-landmark","color":"#fcd34d"},
    "nantes":            {"img": pimg(130), "grad": "linear-gradient(135deg,#052e16,#065f46)",
                          "tags":["Machines île","Culture","Gastronomie"],"icon":"fa-solid fa-masks-theater","color":"#6ee7b7"},
    "st-nazaire":        {"img": pimg(116), "grad": "linear-gradient(135deg,#0a1a35,#1e3a6e)",
                          "tags":["Pont","Mer","Chantiers navals"],"icon":"fa-solid fa-bridge-water","color":"#a5b4fc"},
    "saint-nazaire":     {"img": pimg(116), "grad": "linear-gradient(135deg,#0a1a35,#1e3a6e)",
                          "tags":["Pont","Mer","Chantiers navals"],"icon":"fa-solid fa-bridge-water","color":"#a5b4fc"},
    "la baule-escoublac":{"img": pimg(169), "grad": "linear-gradient(135deg,#062040,#0d4580)",
                          "tags":["Grande Plage","Mer","Casino"],"icon":"fa-solid fa-umbrella-beach","color":"#7dd3fc"},
    "le pouliguen":      {"img": pimg(76),  "grad": "linear-gradient(135deg,#063a3a,#0d6e6e)",
                          "tags":["Port","Voile","Côte sauvage"],"icon":"fa-solid fa-sailboat","color":"#67e8f9"},
    "laval":             {"img": pimg(181), "grad": "linear-gradient(135deg,#1e0a40,#3b1580)",
                          "tags":["Château","Art naïf","Mayenne"],"icon":"fa-solid fa-palette","color":"#c4b5fd"},
    "le croisic":        {"img": pimg(74),  "grad": "linear-gradient(135deg,#06253a,#0d4d6b)",
                          "tags":["Port","Pêche","Sel Guérande"],"icon":"fa-solid fa-fish","color":"#7dd3fc"},
    "cholet":            {"img": pimg(583), "grad": "linear-gradient(135deg,#2a0615,#5c0e30)",
                          "tags":["Histoire Vendée","Textiles","Musées"],"icon":"fa-solid fa-building-columns","color":"#f9a8d4"},
    "pornic":            {"img": pimg(76),  "grad": "linear-gradient(135deg,#062040,#0d4580)",
                          "tags":["Plage","Château","Atlantique"],"icon":"fa-solid fa-umbrella-beach","color":"#7dd3fc"},
    "les sables-d'olonne":{"img": pimg(169),"grad": "linear-gradient(135deg,#062040,#0d4580)",
                          "tags":["Plage","Vendée Globe","Mer"],"icon":"fa-solid fa-sailboat","color":"#67e8f9"},
    "la roche-sur-yon":  {"img": pimg(103), "grad": "linear-gradient(135deg,#1a1a2e,#16213e)",
                          "tags":["Ville napoléonienne","Vendée","Histoire"],"icon":"fa-solid fa-landmark","color":"#a5b4fc"},
    "clisson":           {"img": pimg(40),  "grad": "linear-gradient(135deg,#2d1b00,#5c3800)",
                          "tags":["Château","Muscadet","Toscane"],"icon":"fa-solid fa-chess-rook","color":"#fcd34d"},
    "fontenay-le-comte": {"img": pimg(826), "grad": "linear-gradient(135deg,#0a2a0a,#155215)",
                          "tags":["Marais poitevin","Renaissance","Nature"],"icon":"fa-solid fa-leaf","color":"#6ee7b7"},
}

DEST_PHRASES = {
    "nantes":             "La Venise de l'Ouest — vibrante, créative et gastronomique",
    "saumur":             "Le Joyau de l'Anjou — châteaux, vins de Loire et équitation",
    "le mans":            "Ville de Légende — là où l'histoire prend de la vitesse",
    "angers-st-laud":     "Capitale de l'Anjou — douceur de vivre et patrimoine d'exception",
    "angers":             "Capitale de l'Anjou — douceur de vivre et patrimoine d'exception",
    "st-nazaire":         "Porte de l'Atlantique — entre océan infini et épopée industrielle",
    "saint-nazaire":      "Porte de l'Atlantique — entre océan infini et épopée industrielle",
    "la baule-escoublac": "La Plus Belle Baie d'Europe — sable blanc à l'infini",
    "le pouliguen":       "Perle de la Côte d'Amour — ports de pêche, criques et authenticité",
    "laval":              "Cité des Arts Naïfs — étonnante, secrète et pleine de surprises",
    "le croisic":         "Presqu'île de Guérande — sel, mer et saveurs de l'estuaire",
    "cholet":             "Cœur de Vendée — caractère, histoire et esprit de conquête",
    "la roche-sur-yon":   "Ville Napoléonienne — architecture et vitalité vendéenne",
    "les sables-d'olonne":"Station Emblématique — plages infinies et vendée globe",
    "les sables":         "Station Emblématique — plages infinies et vendée globe",
    "pornic":             "Cité Balnéaire de Charme — falaises, plages et château médiéval",
    "ancenis":            "Porte de Bretagne — vignobles, Loire et art de vivre",
    "clisson":            "La Petite Toscane — château médiéval et vignes muscadet",
    "fontenay-le-comte":  "Cité de la Renaissance — histoire, nature et marais poitevin",
    "challans":           "Pays des Variétés — bocage, marais et gastronomie typique",
    "pontchâteau":        "Terre de Pèlerinage — calvaire, nature et traditions bretonnes",
    "redon":              "Carrefour des Rivières — canaux, châtaignes et architecture",
    "blain":              "Presqu'île de Bretagne — château, forêt de Gavre et authenticité",
    "paimboeuf":          "Estuaire Mystérieux — bord de Loire, pêcheurs et patrimoine",
    "sainte-luce-sur-loire": "Porte Est de Nantes — vignobles et berges de Loire",
}

PROFIL_META = {
    "Famille":  {"icon":"fa-solid fa-people-roof","color":"#3b82f6","bg":"rgba(59,130,246,0.14)","desc":"Parcs, activités enfants, nature, grands espaces"},
    "Solo":     {"icon":"fa-solid fa-person-hiking","color":"#8b5cf6","bg":"rgba(139,92,246,0.14)","desc":"Culture, patrimoine, aventure en liberté"},
    "Couple":   {"icon":"fa-solid fa-heart","color":"#ec4899","bg":"rgba(236,72,153,0.14)","desc":"Gastronomie, charme, romantisme, détente"},
    "Groupe":   {"icon":"fa-solid fa-users","color":"#f59e0b","bg":"rgba(245,158,11,0.14)","desc":"Sport, événements, animation, fun collectif"},
    "Éco":      {"icon":"fa-solid fa-seedling","color":"#16a34a","bg":"rgba(22,163,74,0.14)","desc":"Nature, mobilité douce, empreinte minimale"},
}

TRAVELER_TYPES = {
    "Solo":     {"icon":"fa-solid fa-person-hiking","color":"#8b5cf6","bg":"rgba(139,92,246,0.14)"},
    "Couple":   {"icon":"fa-solid fa-heart","color":"#ec4899","bg":"rgba(236,72,153,0.14)"},
    "Famille":  {"icon":"fa-solid fa-people-roof","color":"#3b82f6","bg":"rgba(59,130,246,0.14)"},
    "Groupe":   {"icon":"fa-solid fa-users","color":"#f59e0b","bg":"rgba(245,158,11,0.14)"},
    "Senior":   {"icon":"fa-solid fa-person-cane","color":"#a78bfa","bg":"rgba(167,139,250,0.14)"},
}

CAT_FA = {
    "Hébergement":    ("fa-solid fa-bed","#3b82f6"),
    "Restauration":   ("fa-solid fa-utensils","#ef4444"),
    "Culture":        ("fa-solid fa-masks-theater","#8b5cf6"),
    "Patrimoine":     ("fa-solid fa-landmark","#f59e0b"),
    "Nature":         ("fa-solid fa-leaf","#16a34a"),
    "Loisirs":        ("fa-solid fa-gamepad","#ec4899"),
    "Sport & Loisirs":("fa-solid fa-dumbbell","#f97316"),
}
CAT_CLR = {k: v[1] for k,v in CAT_FA.items()}

MOBILITY_OPTIONS = {
    "Vélo": {"icon":"fa-solid fa-person-biking", "color":"#16a34a", "desc":"Locations et pistes cyclables accessibles"},
    "Transports locaux": {"icon":"fa-solid fa-bus", "color":"#3b82f6", "desc":"Bus, tramways et transports en commun"},
    "Mobilité douce": {"icon":"fa-solid fa-person-walking", "color":"#8b5cf6", "desc":"Marche et découverte à pied"},
    "Taxi/VTC": {"icon":"fa-solid fa-car", "color":"#f59e0b", "desc":"Services de transport à la demande"},
    "E-scooter": {"icon":"fa-solid fa-person-hiking", "color":"#06b6d4", "desc":"Scooters électriques en libre-service"},
}

def get_meta(nom):
    k = str(nom).lower().strip()
    for key, val in DEST_META.items():
        if key in k or k in key:
            phrase = next((v for pk, v in DEST_PHRASES.items() if pk in k or k in pk), "")
            return {**val, "phrase": phrase}
    phrase = next((v for pk, v in DEST_PHRASES.items() if pk in k or k in pk), "Une destination à découvrir en train")
    return {"img": _fimg(k), "grad": f"linear-gradient(135deg,{BLDARK},{BLUE})",
            "tags": [], "icon": "fa-solid fa-train", "color": BLUE, "phrase": phrase}

def fi(cls, col="#fff", sz="1rem", ex=""):
    return f'<i class="{cls}" style="color:{col};font-size:{sz};{ex}"></i>'

try:
    df_dest = load_dest()
except Exception as e:
    st.error(f"Connexion base de données impossible : {e}")
    st.stop()

# ════════════════════════════════════════════════════════════════
# PAGE : DESTINATIONS (Enhanced)
# ════════════════════════════════════════════════════════════════
page = st.session_state.get("page", "accueil")
user = st.session_state.get("user")

if page == "destinations":
    deps_list = sorted([d for d in df_dest['departement'].dropna().unique() if d])
    profs_list = sorted([p for p in df_dest['profil_touristique'].dropna().unique() if p])
    traveler_list = list(TRAVELER_TYPES.keys())
    
    st.markdown("<h2>Explorez les Pays de la Loire</h2>", unsafe_allow_html=True)
    
    # ✅ 1. NEW: Traveler Type Filter
    st.markdown("### Type de voyageur")
    traveler_sel = st.multiselect("Quel type de voyageur êtes-vous?", traveler_list,
                                   default=st.session_state.get("f_traveler", []),
                                   key="ds_traveler")
    st.session_state.f_traveler = traveler_sel
    
    # Existing filters
    fb1, fb2, fb3 = st.columns(3)
    with fb1:
        dep_sel = st.multiselect("Département", deps_list,
                                 default=st.session_state.get("f_dep", []),
                                 key="ds_dep")
    with fb2:
        prof_sel = st.multiselect("Profil touristique", profs_list,
                                  default=st.session_state.get("f_prof", []),
                                  key="ds_prf")
    with fb3:
        srt = st.selectbox("Trier par", ["Score", "Activités", "A → Z"],
                          key="ds_srt")
    
    st.session_state.f_dep = dep_sel
    st.session_state.f_prof = prof_sel
    st.session_state.f_sort = srt
    
    # Display destination cards with traveler type badge
    st.markdown("### Résultats")
    for _, row in df_dest.head(12).iterrows():
        gk = str(row['nom_gare']).lower()
        vil = str(row.get('commune', gk)).title()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{vil}** - {row.get('departement', 'N/A')}")
            st.caption(f"{int(row.get('nb_poi_5km', 0))} activités | Score: {float(row.get('score_attractivite', 0)):.1f}/10")
        with col2:
            if st.button("Explorer", key=f"dest_{gk}"):
                st.session_state.dest_sel = gk
                st.session_state.page = "destination"
                st.rerun()

# ════════════════════════════════════════════════════════════════
# PAGE : DESTINATION DETAIL (Enhanced)
# ════════════════════════════════════════════════════════════════
elif page == "destination":
    gk = st.session_state.get("dest_sel")
    if not gk:
        st.warning("Sélectionnez une destination")
        st.stop()
    
    row_g = df_dest[df_dest['nom_gare'] == gk]
    if row_g.empty:
        st.warning("Destination introuvable")
        st.stop()
    
    row_g = row_g.iloc[0]
    vil = str(row_g.get('commune', gk)).title()
    dep = str(row_g.get('departement', '')).title()
    dist_km = round(((float(row_g['latitude']) - 47.218)**2 + (float(row_g['longitude']) + 1.554)**2)**0.5 * 111, 0)
    co2_train = round(2.4 * dist_km / 1000, 2)
    co2_car = round(218 * dist_km / 1000, 2)
    
    st.markdown(f"## {vil}")
    st.markdown(f"*{dep}*")
    
    # ✅ 2. ENHANCED: Activities organized by category/interest
    st.markdown("### Activités par centre d'intérêt")
    with st.spinner("Chargement des activités..."):
        df_poi = load_poi(gk)
    
    if not df_poi.empty:
        # Group activities by category
        categories = sorted(df_poi['categorie'].dropna().unique())
        
        for cat in categories:
            cat_activities = df_poi[df_poi['categorie'] == cat]
            icon, color = CAT_FA.get(cat, ("fa-solid fa-map-pin", "#6b7280"))
            
            with st.expander(f"{fi(icon, color)} {cat} ({len(cat_activities)} activités)", expanded=False):
                cols = st.columns(3)
                for idx, (_, act) in enumerate(cat_activities.head(9).iterrows()):
                    with cols[idx % 3]:
                        st.markdown(f"""<div class='mobility-card'>
                            <div class='mobility-title'>{act.get('nom', 'Activité')}</div>
                            <div class='mobility-desc'>
                                {fi('fa-solid fa-location-dot', color, '0.7rem')} {act.get('commune', 'N/A')}<br>
                                {fi('fa-solid fa-person-walking', color, '0.7rem')} {float(act.get('distance_gare_km', 0)):.1f} km
                            </div>
                        </div>""", unsafe_allow_html=True)
    
    # ✅ 3. ENHANCED: Prominent SNCF CTA + CO2 Comparison
    st.markdown("---")
    st.markdown("### Voyager responsable")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"<a href='https://www.sncf-connect.com' target='_blank' class='sncf-cta'>"
                   f"{fi('fa-solid fa-train', '#fff', '1.2rem')} Acheter sur SNCF Connect"
                   f"</a>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.8rem; margin-top: 1rem;'>Trajets directs optimisés vers {vil}</p>", unsafe_allow_html=True)
    
    with col2:
        # ✅ 4. CO2 Comparison: Train vs Car
        st.markdown(f"""<div class='co2-compare'>
            <div class='co2-item train'>
                <div class='co2-num' style='color:{CO2GB};'>{co2_train:.1f}</div>
                <div style='font-size:0.7rem;'>{fi('fa-solid fa-train', CO2GB)} Train TER</div>
            </div>
            <div class='co2-item car'>
                <div class='co2-num' style='color:{CO2BB};'>{co2_car:.1f}</div>
                <div style='font-size:0.7rem;'>{fi('fa-solid fa-car', CO2BB)} Voiture</div>
            </div>
        </div>
        <div style='text-align:center; font-size:0.85rem; font-weight:700; color:{GREEN};'>
            {fi('fa-solid fa-leaf', GREEN)} Vous économisez {co2_car - co2_train:.1f} kg CO₂
        </div>""", unsafe_allow_html=True)
    
    # ✅ 5. NEW: Local Mobility & How to Get Around
    st.markdown("---")
    st.markdown("### Comment se déplacer sur place?")
    
    mobility_cols = st.columns(len(MOBILITY_OPTIONS))
    for idx, (mode, details) in enumerate(MOBILITY_OPTIONS.items()):
        with mobility_cols[idx]:
            st.markdown(f"""<div class='mobility-card'>
                <div style='text-align:center; margin-bottom:8px;'>
                    {fi(details['icon'], details['color'], '1.5rem')}
                </div>
                <div class='mobility-title'>{mode}</div>
                <div class='mobility-desc'>{details['desc']}</div>
            </div>""", unsafe_allow_html=True)
    
    st.info("💡 Conseil: Consultez les offices de tourisme locaux pour les bons plans sur la mobilité douce et les tarifs réduits avec votre billet SNCF.")

else:
    st.markdown(f"<h1>Bienvenue sur Wandrail</h1>", unsafe_allow_html=True)
    st.markdown("Découvrez les Pays de la Loire en train de manière responsable.")
    
    if st.button("Explorer les destinations"):
        st.session_state.page = "destinations"
        st.rerun()
