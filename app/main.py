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
                   layout="wide", initial_sidebar_state="collapsed")

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
[data-testid="stSidebar"]{{display:none!important}}
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
  justify-content:space-between;height:68px;box-shadow:0 2px 12px rgba(0,0,0,.06)}}
.tv-brand{{display:flex;align-items:center;gap:10px;font-size:1.08rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;text-decoration:none}}
.tv-brand-dot{{width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,{BLUE},{ACCENT});animation:heroPulse 3s ease-in-out infinite}}
.tv-nav{{display:flex;align-items:center;gap:0;flex:1;justify-content:center}}
.tv-nav-lnk{{padding:0 14px;height:68px;display:flex;align-items:center;font-size:.82rem;
  font-weight:600;color:{TEXT2};text-decoration:none;border-bottom:3px solid transparent;
  transition:all .18s;cursor:pointer;white-space:nowrap}}
.tv-nav-lnk:hover{{color:{BLUE};border-bottom-color:{BLUE}30}}
.tv-nav-lnk.cur{{color:{BLUE};border-bottom-color:{BLUE};font-weight:700}}
.tv-right{{display:flex;align-items:center;gap:12px;margin-left:auto}}
.auth-btn{{background:{BLUE};color:#fff;padding:8px 16px;border-radius:8px;border:none;font-weight:600;font-size:.8rem;cursor:pointer;transition:all .2s}}
.auth-btn:hover{{background:{BLDARK};box-shadow:0 2px 8px {BLUE}40}}
.user-chip{{background:linear-gradient(135deg,{BLUE},{BLDARK});color:#fff;padding:6px 14px;border-radius:20px;font-size:.8rem;font-weight:600;display:flex;align-items:center;gap:7px}}

/* FILTERS CENTER SECTION */
.filters-container{{max-width:1200px;margin:2rem auto;padding:0 2.5rem}}
.filters-header{{font-size:1.3rem;font-weight:800;color:{TEXT};margin-bottom:1.5rem;letter-spacing:-.02em}}
.filters-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.5rem;margin-bottom:2rem}}
.filter-box{{border:1px solid {BORDER};border-radius:12px;padding:1.2rem;background:{CARD};box-shadow:{SHADOW2}}}
.filter-label{{font-size:.75rem;font-weight:700;color:{TEXT2};text-transform:uppercase;letter-spacing:.05em;margin-bottom:.6rem}}

/* ACTIVITY CARD */
.acard{{border:1px solid {BORDER};border-radius:12px;overflow:hidden;background:{CARD};transition:all .2s}}
.acard:hover{{box-shadow:{SHADOW2};border-color:{BORDER2};transform:translateY(-2px)}}
.acard-img{{height:90px;position:relative;overflow:hidden;background:{CARD2}}}
.acard-img img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
.acard-ico{{position:absolute;bottom:4px;right:5px;background:rgba(0,0,0,.45);border-radius:4px;padding:2px 5px}}
.acard-body{{padding:.7rem .85rem .85rem}}
.acard-nm{{font-weight:700;font-size:.81rem;color:{TEXT};margin:0 0 4px;line-height:1.3}}
.acard-mt{{font-size:.68rem;color:{TEXT2};line-height:1.75;margin:0}}

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
}

DEST_PHRASES = {
    "nantes":             "La Venise de l'Ouest — vibrante, créative et gastronomique",
    "saumur":             "Le Joyau de l'Anjou — châteaux, vins de Loire et équitation",
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

page = st.session_state.get("page", "accueil")
user = st.session_state.get("user")

# ── NAVBAR WITH CENTERED NAV + RIGHT AUTH ──────────────────────
auth_chip = ""
if user:
    initials = "".join([w[0].upper() for w in user['pseudo'].split()[:2]])
    auth_chip = f'<div class="user-chip">{fi("fa-solid fa-user", "#fff", "0.8rem")} {user["pseudo"]}</div>'
else:
    auth_chip = f'<button class="auth-btn" onclick="document.getElementById(\"auth_btn\").click()">Se connecter</button>'

nav_links_html = ""
for lbl, pg, ico in [("Accueil","accueil","fa-solid fa-house"), ("Destinations","destinations","fa-solid fa-map"), ("Carte","carte","fa-solid fa-earth-europe")]:
    is_active = page == pg
    nav_links_html += f'<span class="tv-nav-lnk {"cur" if is_active else "}">{lbl}</span>'

st.markdown(f"""<div class="tvnav">
  <div class="tv-brand">
    <div class="tv-brand-dot"></div>
    <span>Wand<span style="color:{BLUE};">rail</span></span>
    <span style="font-weight:400;color:{TEXT2};font-size:.72rem;margin-left:2px;">PDL</span>
  </div>
  <nav class="tv-nav">{nav_links_html}</nav>
  <div class="tv-right">{auth_chip}</div>
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# PAGE : DESTINATIONS (Enhanced - Centered Filters)
# ════════════════════════════════════════════════════════════════
if page == "destinations":
    deps_list = sorted([d for d in df_dest['departement'].dropna().unique() if d])
    profs_list = sorted([p for p in df_dest['profil_touristique'].dropna().unique() if p])
    traveler_list = list(TRAVELER_TYPES.keys())
    
    # CENTERED FILTERS SECTION
    st.markdown(f'<div class="filters-container"><div class="filters-header">Explorez les Pays de la Loire</div>', unsafe_allow_html=True)
    
    # Create responsive filter grid
    fc1, fc2, fc3, fc4 = st.columns(4)
    
    with fc1:
        st.markdown(f'<div class="filter-label">Type de voyageur</div>', unsafe_allow_html=True)
        traveler_sel = st.multiselect("Type de voyageur", traveler_list,
                                       default=st.session_state.get("f_traveler", []),
                                       key="ds_traveler", label_visibility="collapsed")
        st.session_state.f_traveler = traveler_sel
    
    with fc2:
        st.markdown(f'<div class="filter-label">Département</div>', unsafe_allow_html=True)
        dep_sel = st.multiselect("Département", deps_list,
                                 default=st.session_state.get("f_dep", []),
                                 key="ds_dep", label_visibility="collapsed")
        st.session_state.f_dep = dep_sel
    
    with fc3:
        st.markdown(f'<div class="filter-label">Profil touristique</div>', unsafe_allow_html=True)
        prof_sel = st.multiselect("Profil touristique", profs_list,
                                  default=st.session_state.get("f_prof", []),
                                  key="ds_prf", label_visibility="collapsed")
        st.session_state.f_prof = prof_sel
    
    with fc4:
        st.markdown(f'<div class="filter-label">Trier par</div>', unsafe_allow_html=True)
        srt = st.selectbox("Trier par", ["Score", "Activités", "A → Z"],
                          key="ds_srt", label_visibility="collapsed")
        st.session_state.f_sort = srt
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display results
    st.markdown(f'<div style="max-width:1200px;margin:2rem auto;padding:0 2.5rem;font-size:1.1rem;font-weight:700;color:{TEXT};">{len(df_dest)} destinations trouvées</div>', unsafe_allow_html=True)
    
    for idx, (_, row) in enumerate(df_dest.head(12).iterrows()):
        if idx % 3 == 0:
            cols = st.columns(3)
        
        gk = str(row['nom_gare']).lower()
        vil = str(row.get('commune', gk)).title()
        
        with cols[idx % 3]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{vil}**")
                st.caption(f"📍 {row.get('departement', 'N/A')} · {int(row.get('nb_poi_5km', 0))} activités")
            with col2:
                if st.button("→", key=f"dest_{gk}", help="Explorer"):
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
    
    st.markdown(f"<h2 style='padding:2rem 2.5rem 0;'>{vil} - {dep}</h2>", unsafe_allow_html=True)
    
    # ACTIVITES
    st.markdown("<h3 style='padding:1rem 2.5rem 0;'>Activités par centre d'intérêt</h3>", unsafe_allow_html=True)
    with st.spinner("Chargement des activités..."):
        df_poi = load_poi(gk)
    
    if not df_poi.empty:
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
    
    # SNCF CTA + CO2
    st.markdown("---")
    st.markdown("<h3 style='padding:0 2.5rem;'>Voyager responsable</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"<div style='padding:0 2.5rem;'><a href='https://www.sncf-connect.com' target='_blank' class='sncf-cta'>{fi('fa-solid fa-train', '#fff', '1.2rem')} Acheter sur SNCF Connect</a></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""<div style='padding:0 2.5rem;' class='co2-compare'>
            <div class='co2-item train'>
                <div class='co2-num' style='color:{CO2GB};'>{co2_train:.1f}</div>
                <div style='font-size:0.7rem;'>{fi('fa-solid fa-train', CO2GB)} Train TER</div>
            </div>
            <div class='co2-item car'>
                <div class='co2-num' style='color:{CO2BB};'>{co2_car:.1f}</div>
                <div style='font-size:0.7rem;'>{fi('fa-solid fa-car', CO2BB)} Voiture</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    # LOCAL MOBILITY
    st.markdown("---")
    st.markdown("<h3 style='padding:0 2.5rem;'>Comment se déplacer sur place?</h3>", unsafe_allow_html=True)
    
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
    
    st.info("💡 Conseil: Consultez les offices de tourisme locaux pour les bons plans et tarifs réduits.")

else:
    st.markdown(f"<div style='padding:4rem 2.5rem;text-align:center;'><h1>Bienvenue sur Wandrail</h1>", unsafe_allow_html=True)
    st.markdown("Découvrez les Pays de la Loire en train de manière responsable.")
    
    if st.button("Explorer les destinations", use_container_width=False):
        st.session_state.page = "destinations"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
