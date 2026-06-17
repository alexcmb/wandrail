import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
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
    BG="#f4f7fe"; CARD="#ffffff"; CARD2="#eef2fd"; BORDER="rgba(0,0,0,0.07)"
    BORDER2="rgba(0,0,0,0.13)"; TEXT="#0c1535"; TEXT2="#5a6a8a"
    SHADOW="0 8px 32px rgba(30,64,175,.13)"; SHADOW2="0 2px 12px rgba(30,64,175,.08)"
    SBARBG="#ffffff"; INPUT="#f0f4ff"; NAVBG="rgba(255,255,255,0.97)"
    HERO_OV="linear-gradient(165deg,rgba(10,40,100,0.88),rgba(30,100,180,0.55))"
    BADGE_BG="rgba(0,0,0,0.45)"; ECO_BG="linear-gradient(135deg,#d1fae5,#a7f3d0)"
    ECO_NUM="#065f46"; ECO_LBL="#047857"; TILE="CartoDB positron"
    CHART_BG="#ffffff"; CO2GB="#16a34a"; CO2BB="#dc2626"
    TAGBG="#eff6ff"; TAGC="#1d4ed8"; FOOT="#0c1535"

BLUE="#8b5cf6" if dk else "#7c3aed"
BLDARK="#6d28d9" if dk else "#4c1d95"
GREEN="#22c55e" if dk else "#16a34a"
ACCENT="#f472b6"

# ── Fonts + FA ─────────────────────────────────────────────────
components.html("""<script>
(function(){var d=window.parent.document;
function lnk(h){if(!d.querySelector('link[href="'+h+'"]')){var l=d.createElement('link');l.rel='stylesheet';l.href=h;d.head.appendChild(l);}}
lnk('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');
lnk('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
})();
</script>""", height=0)

# ── CSS ────────────────────────────────────────────────────────
st.markdown(f"""<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body,[class*="css"]{{font-family:'Space Grotesk','Plus Jakarta Sans',sans-serif!important}}
[data-testid="stSidebar"]{{background:{SBARBG}!important;border-right:1px solid {BORDER}!important;padding-top:0!important}}
[data-testid="stHeader"]{{display:none!important}}
.main .block-container{{padding:0!important;max-width:100%!important}}
body,.main,[data-testid="stAppViewContainer"]{{background:{BG}!important}}
[data-testid="stVerticalBlock"]{{gap:0!important}}
.stTextInput>div>div>input{{background:{INPUT}!important;border:1.5px solid {BORDER2}!important;
  color:{TEXT}!important;border-radius:10px!important;padding:10px 14px!important;font-size:.9rem!important}}
.stTextInput>div>div>input:focus{{border-color:{BLUE}!important;box-shadow:0 0 0 3px {BLUE}25!important}}
.stTextInput label,.stSelectbox label,.stTextArea label,.stSlider label{{color:{TEXT2}!important;font-size:.78rem!important;font-weight:500!important}}
.stSelectbox>div>div{{background:{INPUT}!important;border:1.5px solid {BORDER2}!important;color:{TEXT}!important;border-radius:10px!important}}
.stTextArea textarea{{background:{INPUT}!important;border:1.5px solid {BORDER2}!important;color:{TEXT}!important;border-radius:10px!important}}
.stSlider>div>div>div>div{{background:{BLUE}!important}}
.stCheckbox span{{color:{TEXT}!important;font-size:.85rem!important}}
.stButton>button{{border-radius:9px!important;font-family:'Plus Jakarta Sans',sans-serif!important;font-weight:600!important;
  font-size:.84rem!important;transition:all .15s!important;border:1.5px solid {BORDER2}!important;
  background:{CARD}!important;color:{TEXT}!important;padding:9px 16px!important}}
.stButton>button:hover{{border-color:{BLUE}!important;color:{BLUE}!important;background:{TAGBG}!important}}
.stButton>button[kind="primary"]{{background:linear-gradient(135deg,{BLUE},{BLDARK})!important;color:#fff!important;border-color:transparent!important}}
.stButton>button[kind="primary"]:hover{{opacity:.88!important}}
.stTabs [data-baseweb="tab-list"]{{background:{CARD2}!important;border-radius:12px!important;padding:3px!important;gap:3px!important;border:1px solid {BORDER}!important}}
.stTabs [data-baseweb="tab"]{{border-radius:9px!important;color:{TEXT2}!important;font-weight:600!important;font-size:.83rem!important;padding:9px 18px!important;background:transparent!important}}
.stTabs [aria-selected="true"]{{background:linear-gradient(135deg,{BLUE},{BLDARK})!important;color:#fff!important}}
.stTabs [data-baseweb="tab-panel"]{{padding:0!important}}
.stSpinner>div{{border-top-color:{BLUE}!important}}

/* NAVBAR */
.tvnav{{position:sticky;top:0;z-index:999;background:{NAVBG};backdrop-filter:blur(16px);
  border-bottom:1px solid {BORDER};padding:0 2.2rem;display:flex;align-items:center;
  justify-content:space-between;height:58px;box-shadow:0 1px 8px rgba(0,0,0,.06)}}
.tv-brand{{display:flex;align-items:center;gap:10px;font-size:1.08rem;font-weight:800;color:{TEXT};letter-spacing:-.03em}}
.tv-brand-dot{{width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,{BLUE},{GREEN})}}

/* HERO */
.hero{{position:relative;min-height:500px;display:flex;align-items:center;overflow:hidden;background:#0a1a3c}}
.hero-img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center}}
.hero-ov{{position:absolute;inset:0;background:{HERO_OV}}}
.hero-cnt{{position:relative;z-index:2;width:100%;max-width:780px;margin:0 auto;padding:4rem 2rem;text-align:center}}
.hero-badge{{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,0.14);
  backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.25);border-radius:24px;
  color:rgba(255,255,255,.92);font-size:.72rem;font-weight:700;padding:6px 15px;
  margin-bottom:1.3rem;letter-spacing:.07em;text-transform:uppercase}}
.hero-h1{{font-size:clamp(2rem,5vw,3.5rem);font-weight:900;color:#fff;line-height:1.06;
  margin-bottom:.8rem;letter-spacing:-.04em;text-shadow:0 2px 20px rgba(0,0,0,.4)}}
.hero-sub{{color:rgba(255,255,255,.72);font-size:.93rem;max-width:500px;margin:0 auto 1.8rem;line-height:1.7}}

/* STATS BAR */
.stats-row{{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid {BORDER}}}
.stat-c{{display:flex;flex-direction:column;align-items:center;padding:1.4rem 1rem;border-right:1px solid {BORDER}}}
.stat-c:last-child{{border-right:none}}
.stat-n{{font-size:1.9rem;font-weight:900;letter-spacing:-.05em;
  background:linear-gradient(135deg,{BLUE},{GREEN});-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text}}
.stat-l{{font-size:.7rem;color:{TEXT2};margin-top:4px;font-weight:500;text-align:center}}

/* SECTION */
.sect{{max-width:1440px;margin:0 auto;padding:2.2rem 2.5rem}}

/* DESTINATION CARD */
.dcard{{border-radius:16px;overflow:hidden;background:{CARD};border:1px solid {BORDER};
  box-shadow:{SHADOW2};transition:all .22s;margin-bottom:.1rem}}
.dcard:hover{{transform:translateY(-5px);box-shadow:{SHADOW};border-color:{BORDER2}}}
.dcard-img{{height:200px;position:relative;overflow:hidden;background:#1e3a8a}}
.dcard-img img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .4s;display:block}}
.dcard:hover .dcard-img img{{transform:scale(1.06)}}
.dcard-ov,.dcard-ov span{{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.72) 0%,transparent 55%);display:block}}
.dcard-badge{{position:absolute;top:10px;left:10px;background:{BADGE_BG};backdrop-filter:blur(10px);
  color:rgba(255,255,255,.9);border-radius:16px;padding:4px 10px;font-size:.66rem;font-weight:700;
  display:inline-flex;align-items:center;gap:5px;border:1px solid rgba(255,255,255,.2)}}
.dcard-score{{position:absolute;top:10px;right:10px;background:rgba(0,0,0,.5);
  backdrop-filter:blur(8px);color:#fcd34d;border-radius:14px;padding:4px 9px;
  font-size:.7rem;font-weight:700;display:inline-flex;align-items:center;gap:4px}}
.dcard-city{{position:absolute;bottom:10px;left:13px;color:#fff;font-size:1.12rem;
  font-weight:800;letter-spacing:-.02em;text-shadow:0 2px 8px rgba(0,0,0,.5);display:block}}
.dcard-body{{padding:.85rem 1.1rem 1rem}}
.dcard-meta{{font-size:.7rem;color:{TEXT2};margin:0 0 8px;display:flex;align-items:center;gap:5px}}
.dtag{{background:{TAGBG};color:{TAGC};border-radius:6px;padding:3px 8px;
  font-size:.64rem;font-weight:600;display:inline-flex;align-items:center;gap:3px}}
.dcard-foot{{display:flex;align-items:center;justify-content:space-between;padding-top:8px;
  border-top:1px solid {BORDER};margin:0}}
.poi-cnt{{font-size:.7rem;color:{TEXT2};display:flex;align-items:center;gap:4px}}

/* ACTIVITY CARD */
.acard{{border:1px solid {BORDER};border-radius:12px;overflow:hidden;background:{CARD};transition:all .18s}}
.acard:hover{{box-shadow:{SHADOW2};border-color:{BORDER2}}}
.acard-img{{height:90px;position:relative;overflow:hidden;background:{CARD2}}}
.acard-img img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
.acard-ico{{position:absolute;bottom:4px;right:5px;background:rgba(0,0,0,.45);border-radius:4px;padding:2px 5px}}
.acard-body{{padding:.7rem .85rem .85rem}}
.acard-nm{{font-weight:700;font-size:.81rem;color:{TEXT};margin:0 0 4px;line-height:1.3}}
.acard-mt{{font-size:.68rem;color:{TEXT2};line-height:1.75;margin:0}}

/* PROFIL CARD */
.pcard{{border:2px solid {BORDER};border-radius:14px;padding:1.4rem .9rem;text-align:center;
  cursor:pointer;transition:all .18s;background:{CARD}}}
.pcard:hover{{border-color:{BLUE};box-shadow:0 0 0 3px {BLUE}18}}
.pcard.sel{{border-color:{BLUE};background:{TAGBG}}}
.p-ico{{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 9px;font-size:1.35rem}}
.p-nm{{font-weight:700;font-size:.88rem;color:{TEXT};margin-bottom:3px}}
.p-ds{{font-size:.68rem;color:{TEXT2};line-height:1.45}}

/* DESTINATION HERO */
.dhero{{height:320px;position:relative;overflow:hidden;display:flex;align-items:flex-end;background:#0a1a3c}}
.dhero img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
.dhero-ov{{position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.86) 0%,rgba(0,0,0,.25) 60%,transparent)}}
.dhero-body{{position:relative;z-index:2;padding:1.6rem 2.2rem;width:100%}}
.dhero-h1{{color:#fff;font-size:2.2rem;font-weight:900;letter-spacing:-.04em;margin-bottom:6px;text-shadow:0 2px 14px rgba(0,0,0,.4)}}
.chip{{background:rgba(255,255,255,.15);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.28);
  border-radius:16px;color:rgba(255,255,255,.92);padding:5px 12px;font-size:.72rem;font-weight:600;
  display:inline-flex;align-items:center;gap:6px}}

/* WEATHER */
.wx-wrap{{background:{'rgba(37,99,235,0.1)' if dk else '#eff6ff'};border:1px solid {'rgba(37,99,235,0.2)' if dk else '#bfdbfe'};
  border-radius:14px;padding:1.2rem;display:flex;align-items:center;gap:1.4rem}}
.wx-day{{text-align:center;background:{CARD};border:1px solid {BORDER};border-radius:10px;padding:.75rem .6rem}}

/* ITINERARY */
.itin-day{{background:{CARD};border:1px solid {BORDER};border-radius:16px;overflow:hidden;margin-bottom:.9rem;box-shadow:{SHADOW2}}}
.itin-hdr{{background:linear-gradient(135deg,{BLDARK},{BLUE});color:#fff;padding:12px 18px;font-weight:700;font-size:.86rem;display:flex;align-items:center;gap:9px}}
.itin-row{{display:flex;align-items:flex-start;gap:13px;padding:12px 18px;border-bottom:1px solid {BORDER}}}
.itin-row:last-child{{border-bottom:none}}
.itin-time{{font-size:.7rem;font-weight:700;color:{BLUE};min-width:46px;padding-top:3px}}
.itin-ico{{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.82rem;flex-shrink:0}}
.itin-tx h4{{margin-bottom:2px;font-size:.83rem;font-weight:700;color:{TEXT}}}
.itin-tx p{{margin:0;font-size:.7rem;color:{TEXT2}}}

/* STEP BAR */
.step-bar{{display:flex;border-bottom:2px solid {BORDER};margin-bottom:1.8rem}}
.step-i{{flex:1;padding:11px;text-align:center;font-size:.78rem;font-weight:600;color:{TEXT2};
  border-bottom:3px solid transparent;margin-bottom:-2px;display:flex;align-items:center;justify-content:center;gap:6px}}
.step-i.act{{color:{BLUE};border-bottom-color:{BLUE}}}
.step-i.done{{color:{GREEN};border-bottom-color:{GREEN}}}
.sn{{width:19px;height:19px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:700}}
.step-i.act .sn{{background:{BLUE};color:#fff}}
.step-i.done .sn{{background:{GREEN};color:#fff}}
.step-i:not(.act):not(.done) .sn{{background:{BORDER2};color:{TEXT2}}}

/* RECO CARD */
.rcard-img{{width:80px;height:58px;border-radius:10px;overflow:hidden;background:{CARD2};flex-shrink:0;position:relative}}
.rcard-img img{{width:100%;height:100%;object-fit:cover;display:block}}
.rcard-rk{{position:absolute;top:3px;left:3px;background:{BLUE};color:#fff;border-radius:5px;padding:2px 6px;font-size:.62rem;font-weight:700}}
.rcard-nm{{font-size:.98rem;font-weight:800;color:{TEXT};margin-bottom:3px;letter-spacing:-.02em}}
.rbar{{height:3px;background:{BORDER};border-radius:2px;overflow:hidden;margin:5px 0 3px}}

/* ECO */
.eco-big{{background:{ECO_BG};border-radius:16px;padding:1.6rem;text-align:center;border:1px solid rgba(52,211,153,.25)}}
.eco-num{{font-size:2.6rem;font-weight:900;letter-spacing:-.04em;color:{ECO_NUM};line-height:1}}
.eco-lbl{{font-size:.82rem;color:{ECO_LBL};margin-top:6px;font-weight:500}}

/* BADGE */
.badge-card{{border:1px solid {BORDER};border-radius:12px;padding:.9rem;text-align:center;background:{CARD}}}
.badge-card.unlocked{{border-color:{BLUE};background:{TAGBG}}}
.badge-card.locked{{opacity:.4}}
.badge-ico{{width:48px;height:48px;border-radius:50%;margin:0 auto 7px;display:flex;align-items:center;justify-content:center;font-size:1.25rem}}

/* REVIEW */
.rev-card{{border:1px solid {BORDER};border-radius:12px;padding:.9rem 1.1rem;background:{CARD};margin-bottom:.65rem}}
.rev-av{{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,{BLUE},{BLDARK});
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:.8rem;font-weight:700;flex-shrink:0}}

/* SIDEBAR NAV */
.sb-nav-btn{{width:100%;display:flex;align-items:center;gap:9px;padding:9px 12px;border-radius:9px;
  font-size:.83rem;font-weight:600;color:{TEXT2};cursor:pointer;transition:all .14s;
  background:transparent;border:none;text-align:left;margin-bottom:2px}}
.sb-nav-btn:hover{{background:{CARD2};color:{TEXT}}}
.sb-nav-btn.active{{background:linear-gradient(135deg,{BLUE},{BLDARK});color:#fff}}

.footer{{background:{FOOT};color:rgba(255,255,255,.3);padding:2rem;text-align:center;font-size:.72rem}}
</style>""", unsafe_allow_html=True)

# ── DB ─────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    # Streamlit Cloud : variable dans st.secrets["DATABASE_URL"]
    # Local : variable dans .env ou fallback localhost
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
    # Picsum photos: consistent image per seed, no API key needed
    clean = seed.replace(' ', '').replace(',', '').replace('+', '').replace("'", '')[:20]
    return f"https://picsum.photos/seed/{clean}/{w}/{h}"

# Hero background — landscape/nature photo that looks like travel
HERO_IMG = "https://picsum.photos/seed/trainvoyagefrance/1920/900"

DEST_META = {
    "saumur":           {"img": uimg("saumurcastle"), "grad": "linear-gradient(135deg,#0f2a5c,#1e4c9e)",
                         "tags":["Château","Vin d'Anjou","Loire"],"icon":"fa-solid fa-chess-rook","color":"#60a5fa"},
    "le mans":          {"img": uimg("lemansrace"), "grad": "linear-gradient(135deg,#4a0f0f,#8b1a1a)",
                         "tags":["Circuit 24H","Cathédrale","Sport"],"icon":"fa-solid fa-flag-checkered","color":"#fca5a5"},
    "angers-st-laud":   {"img": uimg("angerscastle"), "grad": "linear-gradient(135deg,#3d1f06,#7a3d0d)",
                         "tags":["Château","Tapisserie","Maine"],"icon":"fa-solid fa-landmark","color":"#fcd34d"},
    "nantes":           {"img": uimg("nantesvilles"), "grad": "linear-gradient(135deg,#052e16,#065f46)",
                         "tags":["Machines île","Culture","Gastronomie"],"icon":"fa-solid fa-masks-theater","color":"#6ee7b7"},
    "st-nazaire":       {"img": uimg("saintnazaireport"), "grad": "linear-gradient(135deg,#0a1a35,#1e3a6e)",
                         "tags":["Pont","Mer","Chantiers navals"],"icon":"fa-solid fa-bridge-water","color":"#a5b4fc"},
    "la baule-escoublac":{"img": uimg("laBaulebeach"), "grad": "linear-gradient(135deg,#062040,#0d4580)",
                         "tags":["Grande Plage","Mer","Casino"],"icon":"fa-solid fa-umbrella-beach","color":"#7dd3fc"},
    "le pouliguen":     {"img": uimg("lePoulguen"), "grad": "linear-gradient(135deg,#063a3a,#0d6e6e)",
                         "tags":["Port","Voile","Côte sauvage"],"icon":"fa-solid fa-sailboat","color":"#67e8f9"},
    "laval":            {"img": uimg("lavalFrance"), "grad": "linear-gradient(135deg,#1e0a40,#3b1580)",
                         "tags":["Château","Art naïf","Mayenne"],"icon":"fa-solid fa-palette","color":"#c4b5fd"},
    "le croisic":       {"img": uimg("leCroisicport"), "grad": "linear-gradient(135deg,#06253a,#0d4d6b)",
                         "tags":["Port","Pêche","Sel Guérande"],"icon":"fa-solid fa-fish","color":"#7dd3fc"},
    "cholet":           {"img": uimg("choletville"), "grad": "linear-gradient(135deg,#2a0615,#5c0e30)",
                         "tags":["Histoire Vendée","Textiles","Musées"],"icon":"fa-solid fa-building-columns","color":"#f9a8d4"},
}

PROFIL_META = {
    "Famille":  {"icon":"fa-solid fa-people-roof","color":"#3b82f6","bg":"rgba(59,130,246,0.14)","desc":"Parcs, activités enfants, nature, grands espaces"},
    "Solo":     {"icon":"fa-solid fa-person-hiking","color":"#8b5cf6","bg":"rgba(139,92,246,0.14)","desc":"Culture, patrimoine, aventure en liberté"},
    "Couple":   {"icon":"fa-solid fa-heart","color":"#ec4899","bg":"rgba(236,72,153,0.14)","desc":"Gastronomie, charme, romantisme, détente"},
    "Groupe":   {"icon":"fa-solid fa-users","color":"#f59e0b","bg":"rgba(245,158,11,0.14)","desc":"Sport, événements, animation, fun collectif"},
    "Éco":      {"icon":"fa-solid fa-seedling","color":"#16a34a","bg":"rgba(22,163,74,0.14)","desc":"Nature, mobilité douce, empreinte minimale"},
}

BADGES = [
    {"id":"first","name":"Premier Pas","icon":"fa-solid fa-baby","color":"#10b981","bg":"rgba(16,185,129,.14)","desc":"1ère visite enregistrée","fn":lambda v,co2,f:v>=1},
    {"id":"voyageur","name":"Voyageur","icon":"fa-solid fa-train","color":"#3b82f6","bg":"rgba(59,130,246,.14)","desc":"3 destinations visitées","fn":lambda v,co2,f:v>=3},
    {"id":"explorer","name":"Explorateur","icon":"fa-solid fa-map","color":"#8b5cf6","bg":"rgba(139,92,246,.14)","desc":"10 destinations visitées","fn":lambda v,co2,f:v>=10},
    {"id":"eco1","name":"Éco-Conscient","icon":"fa-solid fa-leaf","color":"#10b981","bg":"rgba(16,185,129,.14)","desc":"100 kg CO₂ économisés","fn":lambda v,co2,f:co2>=100},
    {"id":"eco2","name":"Héros Vert","icon":"fa-solid fa-earth-europe","color":"#059669","bg":"rgba(5,150,105,.14)","desc":"500 kg CO₂ économisés","fn":lambda v,co2,f:co2>=500},
    {"id":"eco3","name":"Légende Planète","icon":"fa-solid fa-globe","color":"#047857","bg":"rgba(4,120,87,.14)","desc":"1 tonne CO₂ économisée","fn":lambda v,co2,f:co2>=1000},
    {"id":"fan","name":"Fan PDL","icon":"fa-solid fa-star","color":"#f59e0b","bg":"rgba(245,158,11,.14)","desc":"5 destinations en favoris","fn":lambda v,co2,f:f>=5},
]

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

def get_meta(nom):
    k = str(nom).lower().strip()
    for key, val in DEST_META.items():
        if key in k or k in key: return val
    return {"img": uimg(k), "grad": f"linear-gradient(135deg,{BLDARK},{BLUE})",
            "tags": [], "icon": "fa-solid fa-train", "color": BLUE}

def fi(cls, col="#fff", sz="1rem", ex=""):
    return f'<i class="{cls}" style="color:{col};font-size:{sz};{ex}"></i>'

try:
    df_dest = load_dest()
except Exception as e:
    st.error(f"Connexion base de données impossible : {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""<div style="padding:.8rem 0 .6rem;">
      <div style="display:flex;align-items:center;gap:9px;">
        <div style="width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,{BLUE},{BLDARK});
          display:flex;align-items:center;justify-content:center;">
          {fi("fa-solid fa-train","#fff","0.78rem")}
        </div>
        <div>
          <div style="font-size:.92rem;font-weight:800;color:{TEXT};letter-spacing:-.02em;">Wandrail</div>
          <div style="font-size:.62rem;color:{TEXT2};margin-top:1px;">Pays de la Loire</div>
        </div>
      </div>
    </div>
    <div style="height:1px;background:{BORDER};margin:.5rem 0;"></div>""", unsafe_allow_html=True)

    user = st.session_state.user

    if user is None:
        tab_l, tab_r = st.tabs(["Connexion", "Inscription"])
        with tab_l:
            with st.form("login_form"):
                em = st.text_input("Email", placeholder="votre@email.com")
                pw = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter", type="primary", use_container_width=True):
                    u, err = login_user(em, pw)
                    if u: st.session_state.user = u; st.rerun()
                    else: st.error(err)
        with tab_r:
            with st.form("reg_form"):
                r_em = st.text_input("Email", placeholder="votre@email.com", key="reg_em")
                r_ps = st.text_input("Pseudo", placeholder="VoyageurPDL", key="reg_ps")
                r_vl = st.text_input("Ville de départ", value="Nantes", key="reg_vl")
                r_pw = st.text_input("Mot de passe", type="password", key="reg_pw")
                if st.form_submit_button("Créer mon compte", type="primary", use_container_width=True):
                    ok, err = register_user(r_em, r_ps, r_pw, r_vl)
                    if ok:
                        u, _ = login_user(r_em, r_pw)
                        st.session_state.user = u; st.rerun()
                    else: st.error(err)
    else:
        initials = "".join([w[0].upper() for w in user['pseudo'].split()[:2]])
        visits, favs, revs = get_user_stats(user['id'])
        nb_v = len(visits); co2_tot = float(visits['co2_saved_kg'].sum()) if nb_v > 0 else 0
        nb_f = len(favs)
        st.markdown(f"""<div style="background:linear-gradient(135deg,{BLUE},{BLDARK});border-radius:12px;padding:1rem;text-align:center;margin-bottom:.7rem;">
          <div style="width:48px;height:48px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;
            justify-content:center;margin:0 auto 8px;font-size:1.1rem;font-weight:800;color:#fff;">{initials}</div>
          <div style="color:#fff;font-weight:700;font-size:.9rem;">{user['pseudo']}</div>
          <div style="color:rgba(255,255,255,.6);font-size:.65rem;margin-top:2px;">{user['ville_depart']}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:.6rem;">
          <div style="background:{CARD};border:1px solid {BORDER};border-radius:8px;padding:.5rem;text-align:center;">
            <div style="font-size:1rem;font-weight:800;color:{BLUE};">{nb_v}</div>
            <div style="font-size:.6rem;color:{TEXT2};">Visites</div>
          </div>
          <div style="background:{CARD};border:1px solid {BORDER};border-radius:8px;padding:.5rem;text-align:center;">
            <div style="font-size:1rem;font-weight:800;color:{GREEN};">{co2_tot:.0f}</div>
            <div style="font-size:.6rem;color:{TEXT2};">kg CO₂</div>
          </div>
          <div style="background:{CARD};border:1px solid {BORDER};border-radius:8px;padding:.5rem;text-align:center;">
            <div style="font-size:1rem;font-weight:800;color:#ec4899;">{nb_f}</div>
            <div style="font-size:.6rem;color:{TEXT2};">Favoris</div>
          </div>
          <div style="background:{CARD};border:1px solid {BORDER};border-radius:8px;padding:.5rem;text-align:center;">
            <div style="font-size:1rem;font-weight:800;color:{ACCENT};">{len(revs)}</div>
            <div style="font-size:.6rem;color:{TEXT2};">Avis</div>
          </div>
        </div>""", unsafe_allow_html=True)
        unlocked = [b for b in BADGES if b['fn'](nb_v, co2_tot, nb_f)]
        if unlocked:
            chips = "".join([f'<div style="display:flex;align-items:center;gap:7px;background:{b["bg"]};border-radius:8px;padding:.4rem .7rem;margin-bottom:.25rem;">{fi(b["icon"],b["color"],"0.82rem")}<span style="font-size:.7rem;font-weight:700;color:{TEXT};">{b["name"]}</span></div>' for b in unlocked[:3]])
            st.markdown(f'<div style="font-size:.7rem;font-weight:700;color:{TEXT2};margin-bottom:.3rem;">Badges</div>{chips}', unsafe_allow_html=True)
        if st.button("Mon profil complet", use_container_width=True):
            st.session_state.page = "profil"; st.rerun()
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.user = None; st.rerun()

    st.markdown(f'<div style="height:1px;background:{BORDER};margin:.6rem 0;"></div>', unsafe_allow_html=True)

    NAV = [
        ("Accueil","accueil","fa-solid fa-house"),
        ("Destinations","destinations","fa-solid fa-map"),
        ("Mon Voyage","planner","fa-solid fa-route"),
        ("Éco-Impact","eco","fa-solid fa-leaf"),
        ("Carte","carte","fa-solid fa-earth-europe"),
    ]
    for lbl, pg, ico in NAV:
        active = st.session_state.page == pg
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;padding:9px 10px;border-radius:9px;
          margin-bottom:2px;cursor:pointer;
          {'background:linear-gradient(135deg,'+BLUE+','+BLDARK+');' if active else 'background:transparent;'}
          transition:all .14s;">
          {fi(ico, "#fff" if active else TEXT2, "0.82rem")}
          <span style="font-size:.83rem;font-weight:{'700' if active else '500'};color:{'#fff' if active else TEXT2};">{lbl}</span>
        </div>""", unsafe_allow_html=True)
        if st.button(lbl, key=f"sb_{pg}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = pg; st.rerun()

    st.markdown('<div style="height:.3rem;"></div>', unsafe_allow_html=True)
    mode_lbl = "Mode clair" if dk else "Mode sombre"
    if st.button(mode_lbl, use_container_width=True):
        st.session_state.dark_mode = not dk; st.rerun()

page = st.session_state.page
user = st.session_state.user

# ── NAVBAR ──────────────────────────────────────────────────────
user_chip = (f'<span style="background:{TAGBG};border:1px solid {BLUE}30;border-radius:16px;'
             f'padding:4px 11px;font-size:.73rem;font-weight:600;color:{BLUE};">'
             f'{fi("fa-regular fa-user",BLUE,"0.68rem")} {user["pseudo"]}</span>') if user else \
            f'<span style="font-size:.73rem;color:{TEXT2};">Non connecté</span>'

st.markdown(f"""<div class="tvnav">
  <div class="tv-brand">
    <div class="tv-brand-dot"></div>
    Wand<span style="color:{BLUE};">rail</span>
    <span style="font-weight:400;color:{TEXT2};font-size:.75rem;margin-left:4px;">Pays de la Loire</span>
  </div>
  {user_chip}
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE : ACCUEIL
# ══════════════════════════════════════════════════════════════════
if page == "accueil":
    st.markdown(f"""<div class="hero">
      <img class="hero-img" src="{HERO_IMG}" alt="Paysage Pays de la Loire" loading="eager">
      <div class="hero-ov"></div>
      <div class="hero-cnt">
        <div class="hero-badge">{fi("fa-solid fa-train","rgba(255,255,255,.9)","0.7rem")} Pays de la Loire &nbsp;·&nbsp; Tourisme en train</div>
        <h1 class="hero-h1">Découvrez les Pays de la Loire<br>autrement</h1>
        <p class="hero-sub">136 gares · 26&thinsp;099 lieux uniques · Votre prochain coup de coeur, à portée de train</p>
      </div>
    </div>""", unsafe_allow_html=True)

    sc1, sc2 = st.columns([5, 1])
    with sc1: q_h = st.text_input("", placeholder="Rechercher une destination...", key="hs", label_visibility="collapsed")
    with sc2:
        if st.button("Rechercher", type="primary", use_container_width=True):
            st.session_state.search_q = q_h; st.session_state.page = "destinations"; st.rerun()

    st.markdown(f"""<div class="stats-row">
      <div class="stat-c"><div class="stat-n">136</div><div class="stat-l">{fi("fa-solid fa-train",TEXT2,"0.68rem")} Gares PDL</div></div>
      <div class="stat-c"><div class="stat-n">26 099</div><div class="stat-l">{fi("fa-solid fa-map-pin",TEXT2,"0.68rem")} Lieux à explorer</div></div>
      <div class="stat-c"><div class="stat-n">−91%</div><div class="stat-l">{fi("fa-solid fa-leaf",TEXT2,"0.68rem")} CO₂ vs voiture</div></div>
      <div class="stat-c"><div class="stat-n">5</div><div class="stat-l">{fi("fa-solid fa-users",TEXT2,"0.68rem")} Styles de voyage</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="sect" style="padding-bottom:0;">
      <div style="display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:1.5rem;">
        <div>
          <div style="font-size:1.3rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;">{fi("fa-solid fa-trophy",ACCENT,"0.95rem")} Destinations incontournables</div>
          <div style="font-size:.78rem;color:{TEXT2};margin-top:3px;">Sélection sur mesure · attractivité + accessibilité train</div></div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    c3 = st.columns(3)
    for i, (_, row) in enumerate(df_dest.head(9).iterrows()):
        gk = str(row['nom_gare']).lower(); meta = get_meta(gk)
        vil = str(row.get('commune', row['nom_gare'])).title()
        sc_ = float(row.get('score_attractivite', 0) or 0)
        np_ = int(row.get('nb_poi_5km', 0) or 0)
        dep = str(row.get('departement', '')).title()
        prf = str(row.get('profil_touristique', ''))
        tgs = "".join([f'<span class="dtag">{t}</span>' for t in meta['tags'][:3]])
        fv = is_fav(user['id'], gk) if user else False
        with c3[i % 3]:
            st.markdown(
                f'<div class="dcard">'
                f'<div class="dcard-img" style="background:{meta["grad"]};">'
                f'<img src="{meta["img"]}" alt="{vil}" loading="lazy">'
                f'<span class="dcard-ov"></span>'
                f'<span class="dcard-badge">{fi(meta["icon"],meta["color"],"0.65rem")} {prf}</span>'
                f'<span class="dcard-score">{fi("fa-solid fa-star","#fcd34d","0.67rem")} {sc_:.1f}</span>'
                f'<span class="dcard-city">{vil}</span>'
                f'</div>'
                f'<div class="dcard-body">'
                f'<p class="dcard-meta">{fi("fa-solid fa-location-dot",TEXT2,"0.67rem")} {dep}</p>'
                f'<p style="display:flex;gap:4px;flex-wrap:wrap;margin:0 0 8px;">{tgs}</p>'
                f'<p class="dcard-foot"><span class="poi-cnt">{fi("fa-solid fa-map-pin",TEXT2,"0.65rem")} {np_} activités</span>'
                f'<span>{fi("fa-solid fa-heart" if fv else "fa-regular fa-heart","#ec4899" if fv else TEXT2,"0.75rem")}</span></p>'
                f'</div></div>',
                unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("Explorer", key=f"h_e_{i}", use_container_width=True, type="primary"):
                    st.session_state.dest_sel = gk; st.session_state.page = "destination"; st.rerun()
            with bc2:
                fv_lbl = "Retirer" if fv else "Favori"
                if st.button(fv_lbl, key=f"h_f_{i}", use_container_width=True):
                    if user: toggle_fav(user['id'], gk); st.rerun()
                    else: st.toast("Connectez-vous pour ajouter des favoris")

    st.markdown(f"""<div style="background:{CARD2};border-top:1px solid {BORDER};padding:2rem 2.5rem;margin-top:1.5rem;">
      <div style="max-width:1440px;margin:0 auto;">
        <div style="font-size:1.2rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;margin-bottom:3px;">{fi("fa-solid fa-wand-magic-sparkles",BLUE,"0.9rem")} Quel voyageur êtes-vous ?</div>
        <div style="font-size:.78rem;color:{TEXT2};margin-bottom:1.4rem;">Votre style de voyage révélé — des recommandations taillées pour vous</div>
      </div>
    </div>""", unsafe_allow_html=True)
    pc = st.columns(5)
    for i, (pn, pd_) in enumerate(PROFIL_META.items()):
        with pc[i]:
            sel = st.session_state.profil_sel == pn
            st.markdown(f"""<div class="pcard {'sel' if sel else ''}">
              <div class="p-ico" style="background:{pd_['bg']};">{fi(pd_['icon'],pd_['color'],"1.3rem")}</div>
              <div class="p-nm">{pn}</div>
              <div class="p-ds">{pd_['desc']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Choisi" if sel else "Choisir", key=f"hp_{pn}", use_container_width=True,
                         type="primary" if sel else "secondary"):
                st.session_state.profil_sel = pn; st.session_state.page = "planner"
                st.session_state.planner_step = 2; st.rerun()

# ══════════════════════════════════════════════════════════════════
# PAGE : DESTINATIONS
# ══════════════════════════════════════════════════════════════════
elif page == "destinations":
    st.markdown(f"""<div class="sect">
      <div style="font-size:1.3rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;margin-bottom:3px;">{fi("fa-solid fa-map",BLUE,"0.95rem")} Toutes les destinations</div>
      <div style="font-size:.78rem;color:{TEXT2};margin-bottom:1.2rem;">{len(df_dest)} gares · Pays de la Loire</div>
    </div>""", unsafe_allow_html=True)

    dc1, dc2, dc3 = st.columns([3, 2, 1])
    with dc1: q = st.text_input("", placeholder="Rechercher...", value=st.session_state.get("search_q",""), key="ds_q", label_visibility="collapsed")
    with dc2: srt = st.selectbox("", ["Popularité", "Activités", "A → Z"], key="ds_s", label_visibility="collapsed")
    with dc3: nb = st.selectbox("", [12, 24, 48, 100], key="ds_n", label_visibility="collapsed")

    df_s = df_dest.copy()
    if q:
        m = (df_s['nom_gare'].str.lower().str.contains(q.lower(), na=False) |
             df_s['commune'].str.lower().str.contains(q.lower(), na=False) |
             df_s['departement'].str.lower().str.contains(q.lower(), na=False))
        df_s = df_s[m]
    if srt == "Activités": df_s = df_s.sort_values('nb_poi_5km', ascending=False)
    elif srt == "Popularité": pass
    elif srt == "A → Z": df_s = df_s.sort_values('commune')
    df_s = df_s.head(int(nb))
    st.markdown(f"<div style='padding:0 2.5rem .8rem;font-size:.75rem;color:{TEXT2};'>{fi('fa-solid fa-filter',TEXT2,'0.67rem')} {len(df_s)} résultats</div>", unsafe_allow_html=True)

    for chunk in [df_s.iloc[i:i+3] for i in range(0, len(df_s), 3)]:
        rc = st.columns(3)
        for ci, (_, row) in enumerate(chunk.iterrows()):
            gk = str(row['nom_gare']).lower(); meta = get_meta(gk)
            vil = str(row.get('commune', row['nom_gare'])).title()
            sc_ = float(row.get('score_attractivite', 0) or 0)
            np_ = int(row.get('nb_poi_5km', 0) or 0)
            dep = str(row.get('departement', '')).title()
            prf = str(row.get('profil_touristique', ''))
            tgs = "".join([f'<span class="dtag">{t}</span>' for t in meta['tags'][:3]])
            fv = is_fav(user['id'], gk) if user else False
            with rc[ci]:
                st.markdown(f"""<div class="sect" style="padding:0 0 .2rem;max-width:100%;">
                  <div class="dcard">
                    <div class="dcard-img" style="background:{meta['grad']};">
                      <img src="{meta['img']}" alt="{vil}" loading="lazy">
                      <div class="dcard-ov"></div>
                      <div class="dcard-badge">{fi(meta['icon'],meta['color'],"0.65rem")} {prf}</div>
                      <div class="dcard-score">{fi("fa-solid fa-star","#fcd34d","0.67rem")} {sc_:.1f}</div>
                      <div class="dcard-city">{vil}</div>
                    </div>
                    <div class="dcard-body">
                      <div class="dcard-meta">{fi("fa-solid fa-location-dot",TEXT2,"0.67rem")} {dep}</div>
                      <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;">{tgs}</div>
                      <div class="dcard-foot">
                        <span class="poi-cnt">{fi("fa-solid fa-map-pin",TEXT2,"0.65rem")} {np_} activités</span>
                        <span style="font-size:.75rem;">{fi("fa-solid fa-heart" if fv else "fa-regular fa-heart","#ec4899" if fv else TEXT2,"0.75rem")}</span>
                      </div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Explorer", key=f"da_{gk[:8]}_{ci}", use_container_width=True, type="primary"):
                        st.session_state.dest_sel = gk; st.session_state.page = "destination"; st.rerun()
                with bc2:
                    if st.button("Retirer" if fv else "Favori", key=f"df_{gk[:8]}_{ci}", use_container_width=True):
                        if user: toggle_fav(user['id'], gk); st.rerun()
                        else: st.toast("Connectez-vous")

# ══════════════════════════════════════════════════════════════════
# PAGE : DESTINATION DÉTAIL
# ══════════════════════════════════════════════════════════════════
elif page == "destination":
    gk = st.session_state.dest_sel
    if not gk: st.session_state.page = "destinations"; st.rerun()
    row_g = df_dest[df_dest['nom_gare'] == gk]
    if row_g.empty: st.warning("Destination introuvable."); st.stop()
    row_g = row_g.iloc[0]; meta = get_meta(gk)
    vil = str(row_g.get('commune', gk)).title()
    dep = str(row_g.get('departement', '')).title()
    sc_ = float(row_g.get('score_attractivite', 0) or 0)
    prf = str(row_g.get('profil_touristique', ''))
    nb5 = int(row_g.get('nb_poi_5km', 0) or 0)
    lat = float(row_g['latitude']); lon = float(row_g['longitude'])
    dist_km = round(((lat - 47.218)**2 + (lon + 1.554)**2)**0.5 * 111, 0)
    co2_sv = round((218 - 2.4) * dist_km * 2 / 1000, 1)
    fv = is_fav(user['id'], gk) if user else False

    b1, _ = st.columns([1, 9])
    with b1:
        if st.button("Retour", key="bk"): st.session_state.page = "destinations"; st.rerun()

    st.markdown(f"""<div class="dhero" style="{'background:'+meta['grad'] if True else ''}">
      <img src="{meta['img']}" alt="{vil}">
      <div class="dhero-ov"></div>
      <div class="dhero-body">
        <div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:7px;">
          <span class="chip">{fi(meta['icon'],meta['color'],"0.72rem")} {prf}</span>
          <span class="chip">{fi("fa-solid fa-star","#fcd34d","0.72rem")} {sc_:.2f}/10</span>
          <span class="chip">{fi("fa-solid fa-map-pin","rgba(255,255,255,.85)","0.72rem")} {nb5} activités</span>
          <span class="chip">{fi("fa-solid fa-train","rgba(255,255,255,.85)","0.72rem")} ~{dist_km:.0f} km</span>
        </div>
        <div class="dhero-h1">{vil}</div>
        <div style="color:rgba(255,255,255,.6);font-size:.82rem;margin-top:3px;">{fi("fa-solid fa-location-dot","rgba(255,255,255,.5)","0.72rem")} {dep}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        fv_txt = "Retirer des favoris" if fv else "Ajouter aux favoris"
        if st.button(fv_txt, use_container_width=True, key="d_fv"):
            if user: toggle_fav(user['id'], gk); st.rerun()
            else: st.toast("Connectez-vous d'abord")
    with ac2:
        if st.button(f"J'ai visité  (−{co2_sv} kg CO₂)", use_container_width=True, type="primary", key="d_vt"):
            if user: log_visit(user['id'], gk, co2_sv, dist_km); st.toast(f"+{co2_sv} kg CO₂ économisés !"); st.rerun()
            else: st.toast("Connectez-vous d'abord")
    with ac3:
        if st.button("Planifier ce voyage", use_container_width=True, key="d_pl"):
            st.session_state.dest_sel = gk; st.session_state.planner_step = 3
            st.session_state.page = "planner"; st.rerun()

    with st.spinner("Chargement des activités..."):
        df_poi = load_poi(gk)

    t1, t2, t3, t4, t5, t6 = st.tabs([
        f"Activités ({len(df_poi)})", "Météo", "Carte", "Mon Itinéraire", "Éco-impact", "Avis"
    ])

    with t1:
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        cats = sorted(df_poi['categorie'].dropna().unique())
        sk = f"cs_{gk[:6]}"
        if sk not in st.session_state: st.session_state[sk] = "Tout"
        all_c = ["Tout"] + list(cats)
        cc = st.columns(min(len(all_c), 8))
        for ci, cat in enumerate(all_c[:8]):
            with cc[ci]:
                if st.button(cat, key=f"cc_{ci}_{gk[:5]}", use_container_width=True,
                             type="primary" if st.session_state[sk] == cat else "secondary"):
                    st.session_state[sk] = cat; st.rerun()
        dv = st.slider("Distance max (km)", 1, 10, 5, key=f"dv_{gk[:6]}")
        df_a = df_poi.copy()
        if st.session_state[sk] != "Tout": df_a = df_a[df_a['categorie'] == st.session_state[sk]]
        df_a = df_a[df_a['distance_gare_km'] <= dv]
        st.markdown(f"<div style='font-size:.72rem;color:{TEXT2};margin:.4rem 0 .7rem;'>{fi('fa-solid fa-filter',TEXT2,'0.67rem')} {len(df_a)} résultats</div>", unsafe_allow_html=True)

        # Render rows of 4 cards in ONE markdown call (CSS grid) to avoid Streamlit div-close bug
        for batch_i, start in enumerate(range(0, min(len(df_a), 48), 4)):
            batch = df_a.iloc[start:start+4]
            row_html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:10px;">'
            for ai, (_, act) in enumerate(batch.iterrows()):
                cat_ = str(act.get('categorie', ''))
                fac, fol = CAT_FA.get(cat_, ("fa-solid fa-map-pin", "#6b7280"))
                dist_ = float(act.get('distance_gare_km', 0) or 0)
                mins = int(act.get('temps_marche_min', 0) or 0)
                note = act.get('note_moyenne')
                note_html = f'<br>{fi("fa-solid fa-star","#fcd34d","0.62rem")} {float(note):.1f}' if note and float(note) > 0 else ''
                img_url = uimg(f"{cat_.replace(' ','')}{batch_i}{gk[:5]}", 400, 200)
                nom = str(act.get('nom', ''))[:42]
                comm = str(act.get('commune', '—')).title()
                row_html += (
                    f'<div class="acard">'
                    f'<div class="acard-img" style="background:{fol}18;">'
                    f'<img src="{img_url}" alt="{cat_}" loading="lazy">'
                    f'<span class="acard-ico">{fi(fac,fol,"0.68rem")}</span>'
                    f'</div>'
                    f'<div class="acard-body">'
                    f'<p class="acard-nm">{nom}</p>'
                    f'<p class="acard-mt">{fi("fa-solid fa-location-dot",TEXT2,"0.62rem")} {comm}<br>'
                    f'{fi("fa-solid fa-person-walking",TEXT2,"0.62rem")} {dist_:.1f} km · {mins} min{note_html}</p>'
                    f'</div>'
                    f'</div>'
                )
            row_html += '</div>'
            st.markdown(row_html, unsafe_allow_html=True)

    with t2:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        commune_nom = str(row_g.get('commune', vil))
        with st.spinner("Chargement météo..."):
            wx = get_weather(commune_nom)
        if wx:
            wc1, wc2 = st.columns([2, 3])
            with wc1:
                st.markdown(f"""<div class="wx-wrap">
                  <div style="font-size:2.6rem;">{fi(wx['icon'],wx['color'],'2.6rem')}</div>
                  <div>
                    <div style="font-size:2.8rem;font-weight:900;color:{TEXT};line-height:1;letter-spacing:-.05em;">{wx['temp']}°<span style="font-size:1rem;">C</span></div>
                    <div style="font-size:.76rem;color:{TEXT2};margin-top:2px;">{wx['desc']}</div>
                    <div style="font-size:.7rem;color:{TEXT2};margin-top:5px;display:flex;gap:10px;">
                      <span>{fi("fa-solid fa-wind",TEXT2,"0.65rem")} {wx['wind']} km/h</span>
                      <span>{fi("fa-solid fa-droplet",TEXT2,"0.65rem")} {wx['humidity']}%</span>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            with wc2:
                if wx.get('days'):
                    dc_ = st.columns(len(wx['days']))
                    for di, day in enumerate(wx['days']):
                        with dc_[di]:
                            st.markdown(f"""<div class="wx-day">
                              <div style="font-size:.66rem;color:{TEXT2};font-weight:600;margin-bottom:4px;">{day.get('date','')[5:] or f'J+{di}'}</div>
                              <div style="font-size:.9rem;margin:.25rem 0;">{fi(wx['icon'],wx['color'],'0.9rem')}</div>
                              <div style="font-size:.84rem;font-weight:700;color:{TEXT};">{day['max']}° / {day['min']}°</div>
                              <div style="font-size:.6rem;color:{TEXT2};margin-top:2px;">{day['desc'][:16]}</div>
                            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="margin-top:.8rem;background:{'rgba(245,158,11,.08)' if dk else '#fefce8'};border:1px solid {'rgba(245,158,11,.25)' if dk else '#fde68a'};border-radius:10px;padding:.8rem 1.1rem;font-size:.78rem;color:{TEXT2};">
              {fi("fa-solid fa-sun",ACCENT,"0.74rem")} Meilleure période : <b style="color:{TEXT};">Mai–Septembre</b> pour les activités de plein air
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Météo temporairement indisponible.")

    with t3:
        m_d = folium.Map(location=[lat, lon], zoom_start=13, tiles=TILE)
        folium.Marker([lat, lon], icon=folium.DivIcon(
            html=f'<div style="background:{BLUE};color:#fff;padding:4px 11px;border-radius:7px;font-size:11px;font-weight:700;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.3);">Gare de {vil}</div>',
            icon_size=(160, 28), icon_anchor=(80, 14))).add_to(m_d)
        folium.Circle([lat, lon], radius=5000, color=BLUE, fill=True, fill_opacity=0.05, weight=1.5, dash_array='6').add_to(m_d)
        cl = MarkerCluster()
        for _, p in df_poi.head(300).iterrows():
            c = CAT_CLR.get(str(p.get('categorie', '')), '#6b7280')
            folium.CircleMarker([p['latitude'], p['longitude']], radius=6, color=c, fill=True,
                fill_opacity=0.85, weight=1,
                popup=f"<b>{p.get('nom','')}</b><br>{p.get('categorie','')}",
                tooltip=str(p.get('nom', ''))[:36]).add_to(cl)
        cl.add_to(m_d)
        st_folium(m_d, width=None, height=480, returned_objects=[])

    with t4:
        def pp(cats, i=0):
            r = df_poi[df_poi['categorie'].isin(cats)]
            return str(r.iloc[i].get('nom', 'Activité'))[:44] if len(r) > i else f"Découverte de {vil}"
        def ir(t_, fac, fol, title, sub):
            return f"""<div class="itin-row"><div class="itin-time">{t_}</div>
              <div class="itin-ico" style="background:{fol}18;">{fi(fac,fol,"0.82rem")}</div>
              <div class="itin-tx"><h4>{title}</h4><p>{sub}</p></div></div>"""
        st.markdown(f"""<div style="max-width:800px;margin:1.2rem auto;padding:0 1.2rem;">
          <div class="itin-day">
            <div class="itin-hdr">{fi("fa-solid fa-sun","#fcd34d")} Jour 1 — Arrivée &amp; découverte</div>
            {ir("10h00","fa-solid fa-train","#3b82f6","Départ en train",f"Voyage responsable · −{co2_sv} kg CO₂")}
            {ir("11h30","fa-solid fa-landmark","#f59e0b",pp(['Patrimoine','Culture']),"Incontournable local")}
            {ir("13h00","fa-solid fa-utensils","#ef4444","Déjeuner local","Spécialités des Pays de la Loire")}
            {ir("14h30","fa-solid fa-masks-theater","#8b5cf6",pp(['Culture']),"Découverte culturelle")}
            {ir("16h30","fa-solid fa-leaf","#16a34a",pp(['Nature']),"Balade &amp; grand air")}
            {ir("20h00","fa-solid fa-bed","#3b82f6",pp(['Hébergement']),f"Nuit à {vil}")}
          </div>
          <div class="itin-day">
            <div class="itin-hdr">{fi("fa-solid fa-cloud-sun","#fcd34d")} Jour 2 — Exploration &amp; retour</div>
            {ir("09h30","fa-solid fa-gamepad","#ec4899",pp(['Loisirs','Sport & Loisirs']),"Activité matinale")}
            {ir("11h00","fa-solid fa-chess-rook","#f59e0b",pp(['Patrimoine'],1),"Patrimoine local")}
            {ir("13h00","fa-solid fa-basket-shopping","#16a34a","Marché local","Produits du terroir")}
            {ir("15h00","fa-solid fa-person-hiking","#16a34a",pp(['Nature'],1),"Détente nature")}
            {ir("17h30","fa-solid fa-train","#3b82f6","Retour en train","Repartez ressourcé")}
          </div>
        </div>""", unsafe_allow_html=True)

    with t5:
        co2_tr = round(2.4 * dist_km / 1000, 2)
        co2_vt = round(218 * dist_km / 1000, 2)
        co2_av = round(258 * dist_km / 1000, 2)
        eco_ = co2_vt - co2_tr; arbr = round(eco_ / 21, 1)
        st.markdown(f"<h4 style='color:{TEXT};padding:1rem 0 .7rem;'>{fi('fa-solid fa-leaf',GREEN,'0.88rem')} Bilan CO₂ — {vil} (~{dist_km:.0f} km)</h4>", unsafe_allow_html=True)
        ec1, ec2, ec3, ec4 = st.columns(4)
        def co2c(lbl, fac, val, good):
            c = CO2GB if good else CO2BB
            return f"""<div style="border:2px solid {c}35;border-radius:13px;padding:1rem;text-align:center;background:{c}0a;">
              <div style="font-size:1.2rem;margin-bottom:6px;">{fi(fac,c,'1.2rem')}</div>
              <div style="font-size:.72rem;color:{TEXT2};margin-bottom:4px;">{lbl}</div>
              <div style="font-size:1.35rem;font-weight:800;color:{c};">{val:.1f} kg</div>
            </div>"""
        with ec1: st.markdown(co2c("Train", "fa-solid fa-train", co2_tr, True), unsafe_allow_html=True)
        with ec2: st.markdown(co2c("Voiture", "fa-solid fa-car", co2_vt, False), unsafe_allow_html=True)
        with ec3: st.markdown(co2c("Avion", "fa-solid fa-plane", co2_av, False), unsafe_allow_html=True)
        with ec4:
            st.markdown(f"""<div class="eco-big">
              <div class="eco-num">−{eco_:.1f}<span style="font-size:.8rem;"> kg</span></div>
              <div class="eco-lbl">{fi("fa-solid fa-leaf",ECO_LBL,"0.75rem")} Train vs Voiture</div>
              <div style="font-size:.7rem;color:{ECO_LBL};margin-top:4px;">{fi("fa-solid fa-tree",ECO_LBL,"0.67rem")} {arbr} arbres</div>
            </div>""", unsafe_allow_html=True)

    with t6:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        revs_df = get_reviews(gk)
        if len(revs_df) > 0:
            avg_r = float(revs_df['rating'].mean()); nb_r_ = len(revs_df)
            stars_full = int(round(avg_r)); stars_empty = 5 - stars_full
            stars_html = fi("fa-solid fa-star","#fcd34d","0.95rem") * stars_full + fi("fa-regular fa-star","#fcd34d","0.95rem") * stars_empty
            rev_cards = "".join([
                f'<div class="rev-card"><div style="display:flex;align-items:center;gap:9px;margin-bottom:6px;">'
                f'<div class="rev-av">{r.pseudo[0].upper()}</div>'
                f'<div style="flex:1;"><b style="color:{TEXT};font-size:.8rem;">{r.pseudo}</b>'
                f'<div style="font-size:.7rem;margin-top:1px;">{fi("fa-solid fa-star","#fcd34d","0.68rem")*int(r.rating)}</div></div>'
                f'<span style="font-size:.62rem;color:{TEXT2};">{str(r.created_at)[:10]}</span>'
                f'</div><div style="font-size:.78rem;color:{TEXT2};">{r.comment or ""}</div></div>'
                for _, r in revs_df.head(5).iterrows()
            ])
            st.markdown(f"""<div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:1rem;
              background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:1.1rem 1.4rem;">
              <div style="text-align:center;min-width:90px;">
                <div style="font-size:2.8rem;font-weight:900;color:{TEXT};line-height:1;">{avg_r:.1f}</div>
                <div style="margin-top:3px;">{stars_html}</div>
                <div style="font-size:.68rem;color:{TEXT2};margin-top:3px;">{nb_r_} avis</div>
              </div>
              <div style="flex:1;border-left:1px solid {BORDER};padding-left:1.4rem;max-height:280px;overflow-y:auto;">
                {rev_cards}
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info(f"Aucun avis pour {vil}. Soyez le premier à en laisser un !")
        if user:
            st.markdown(f"<div style='font-size:.85rem;font-weight:700;color:{TEXT};margin:.5rem 0;'>{fi('fa-solid fa-pen',BLUE,'0.78rem')} Votre avis</div>", unsafe_allow_html=True)
            with st.form("rev_form"):
                rat = st.slider("Note", 1, 5, 4, key="rat_sl")
                com = st.text_area("Commentaire", placeholder=f"Votre expérience à {vil}...", key="rev_com", height=75)
                if st.form_submit_button("Publier", type="primary"):
                    add_review(user['id'], gk, rat, com); st.toast("Avis publié !"); st.rerun()
        else:
            st.info("Connectez-vous pour laisser un avis.")

# ══════════════════════════════════════════════════════════════════
# PAGE : PLANIFICATEUR
# ══════════════════════════════════════════════════════════════════
elif page == "planner":
    step = st.session_state.planner_step
    def sc(n): return "done" if n < step else ("act" if n == step else "")
    st.markdown(f"""<div class="sect">
      <div style="font-size:1.3rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;margin-bottom:1rem;">{fi("fa-solid fa-route",BLUE,"0.95rem")} Planifier mon voyage</div>
      <div class="step-bar">
        <div class="step-i {sc(1)}"><div class="sn">{'✓' if step>1 else '1'}</div> Mon profil</div>
        <div class="step-i {sc(2)}"><div class="sn">{'✓' if step>2 else '2'}</div> Destinations IA</div>
        <div class="step-i {sc(3)}"><div class="sn">3</div> Mon itinéraire</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if step == 1:
        st.markdown(f"<div style='padding:0 2.5rem 1rem;font-size:.87rem;color:{TEXT2};'>Choisissez votre profil pour des recommandations personnalisées</div>", unsafe_allow_html=True)
        pc = st.columns(5)
        for i, (pn, pd_) in enumerate(PROFIL_META.items()):
            with pc[i]:
                sel = st.session_state.profil_sel == pn
                st.markdown(f"""<div class="pcard {'sel' if sel else ''}">
                  <div class="p-ico" style="background:{pd_['bg']};">{fi(pd_['icon'],pd_['color'],"1.35rem")}</div>
                  <div class="p-nm">{pn}</div>
                  <div class="p-ds">{pd_['desc']}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("Choisi" if sel else "Choisir", key=f"pp_{pn}", use_container_width=True,
                             type="primary" if sel else "secondary"):
                    st.session_state.profil_sel = pn; st.rerun()
        if st.session_state.profil_sel:
            _, _, nb_ = st.columns([4, 4, 1])
            with nb_:
                if st.button("Continuer", type="primary", use_container_width=True):
                    st.session_state.planner_step = 2; st.rerun()

    elif step == 2:
        prof = st.session_state.profil_sel
        if not prof: st.session_state.planner_step = 1; st.rerun()
        pd_ = PROFIL_META[prof]
        st.markdown(f"""<div style="max-width:1440px;margin:0 auto;padding:.5rem 2.5rem 1rem;">
          <div style="display:flex;align-items:center;gap:11px;margin-bottom:1rem;">
            <div style="width:42px;height:42px;border-radius:12px;background:{pd_['bg']};display:flex;align-items:center;justify-content:center;">{fi(pd_['icon'],pd_['color'],"1.25rem")}</div>
            <div>
              <div style="font-size:1rem;font-weight:800;color:{TEXT};">Vos 5 destinations — {prof}</div>
              <div style="font-size:.75rem;color:{TEXT2};">Algorithme KNN · Machine Learning</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        with st.spinner("Calcul IA en cours..."):
            df_r = load_reco(prof)
        if df_r.empty:
            st.warning("Aucune recommandation disponible.")
        else:
            for _, rr in df_r.iterrows():
                rgk = str(rr['nom_gare']).lower(); rm = get_meta(rgk)
                rvil = str(rr.get('commune', rr['nom_gare'])).title()
                rsc = float(rr.get('score_attractivite', 0) or 0)
                rscr = float(rr.get('score_reco', 0) or 0); pct = min(100, int(rscr * 10))
                rang = int(rr['rang']); rnp = int(rr.get('nb_poi_5km', 0) or 0)
                tgs = "".join([f'<span class="dtag">{t}</span>' for t in rm['tags'][:3]])
                rc1, rc2, rc3 = st.columns([1, 5, 1])
                with rc1:
                    st.markdown(f"""<div class="rcard-img" style="margin-top:.3rem;background:{rm['grad']};">
                      <img src="{rm['img']}" alt="{rvil}">
                      <div class="rcard-rk">#{rang}</div>
                    </div>""", unsafe_allow_html=True)
                with rc2:
                    st.markdown(f"""<div style="padding:.2rem 0;">
                      <div class="rcard-nm">{fi(rm['icon'],rm['color'],'0.88rem')} {rvil}</div>
                      <div style="display:flex;gap:12px;font-size:.7rem;color:{TEXT2};margin:.3rem 0;">
                        <span>{fi("fa-solid fa-map-pin",TEXT2,"0.65rem")} {rnp} activités</span>
                        <span>{fi("fa-solid fa-star","#fcd34d","0.65rem")} {rsc:.2f}/10</span>
                        <span>{fi("fa-solid fa-brain",BLUE,"0.65rem")} Score IA: {rscr:.2f}/10</span>
                      </div>
                      <div class="rbar"><div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{BLUE},{GREEN});border-radius:2px;"></div></div>
                      <div style="font-size:.7rem;color:{TEXT2};font-style:italic;margin-top:3px;">{rr.get('raison','—')}</div>
                      <div style="margin-top:5px;">{tgs}</div>
                    </div>""", unsafe_allow_html=True)
                with rc3:
                    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                    if st.button("Voir", key=f"re_{rgk[:8]}_{rang}", use_container_width=True):
                        st.session_state.dest_sel = rgk; st.session_state.page = "destination"; st.rerun()
                    if st.button("Choisir", key=f"rc_{rgk[:8]}_{rang}", use_container_width=True, type="primary"):
                        st.session_state.dest_sel = rgk; st.session_state.planner_step = 3; st.rerun()
                st.markdown(f"<div style='height:1px;background:{BORDER};margin:.2rem 0;'></div>", unsafe_allow_html=True)
        pb1, _, pb2 = st.columns([1, 4, 1])
        with pb1:
            if st.button("Profil"): st.session_state.planner_step = 1; st.rerun()
        with pb2:
            if st.session_state.dest_sel:
                if st.button("Générer", type="primary"): st.session_state.planner_step = 3; st.rerun()

    elif step == 3:
        gk = st.session_state.dest_sel
        if not gk: st.session_state.planner_step = 2; st.rerun()
        row_g2 = df_dest[df_dest['nom_gare'] == gk]
        if not row_g2.empty:
            row_g2 = row_g2.iloc[0]; vil2 = str(row_g2.get('commune', gk)).title()
            lat_g = float(row_g2['latitude']); lon_g = float(row_g2['longitude'])
        else: vil2 = gk.title(); lat_g = 47.2; lon_g = -0.5
        meta2 = get_meta(gk); prof2 = st.session_state.profil_sel or "Voyageur"
        dist_km2 = round(((lat_g - 47.218)**2 + (lon_g + 1.554)**2)**0.5 * 111, 0)
        co2_sv2 = round((218 - 2.4) * dist_km2 * 2 / 1000, 1); arbr2 = round(co2_sv2 / 21, 1)
        with st.spinner("Génération..."):
            df_p2 = load_poi(gk)
        def pp2(cats, i=0):
            r = df_p2[df_p2['categorie'].isin(cats)]
            return str(r.iloc[i].get('nom', 'Activité'))[:44] if len(r) > i else f"Activité à {vil2}"
        def ir2(t_, fac, fol, title, sub):
            return f"""<div class="itin-row"><div class="itin-time">{t_}</div>
              <div class="itin-ico" style="background:{fol}18;">{fi(fac,fol,'0.82rem')}</div>
              <div class="itin-tx"><h4>{title}</h4><p>{sub}</p></div></div>"""
        st.markdown(f"""<div style="max-width:840px;margin:1.2rem auto;padding:0 1.5rem;">
          <div style="background:{ECO_BG};border-radius:16px;padding:1.5rem;text-align:center;margin-bottom:1.2rem;border:1px solid rgba(52,211,153,.25);">
            <div style="margin-bottom:7px;">{fi("fa-solid fa-circle-check",ECO_NUM,"1.6rem")}</div>
            <div style="font-size:1.35rem;font-weight:800;color:{ECO_NUM};">Votre voyage est prêt</div>
            <div style="color:{ECO_LBL};margin-top:4px;font-size:.85rem;">{fi(meta2['icon'],meta2['color'])} <b>{vil2}</b> · Profil <b>{prof2}</b></div>
            <div style="color:{ECO_LBL};font-size:.78rem;margin-top:3px;">{fi("fa-solid fa-leaf",ECO_LBL,"0.72rem")} −{co2_sv2} kg CO₂ économisés aller-retour</div>
          </div>
          <div class="itin-day">
            <div class="itin-hdr">{fi("fa-solid fa-sun","#fcd34d")} Jour 1 — Arrivée</div>
            {ir2("10h00","fa-solid fa-train","#3b82f6","Départ en train",f"Vers {vil2}")}
            {ir2("11h30","fa-solid fa-landmark","#f59e0b",pp2(['Patrimoine','Culture']),"Incontournable")}
            {ir2("13h00","fa-solid fa-utensils","#ef4444","Déjeuner local","Spécialités régionales")}
            {ir2("14h30","fa-solid fa-masks-theater","#8b5cf6",pp2(['Culture']),"Culture")}
            {ir2("16h30","fa-solid fa-leaf","#16a34a",pp2(['Nature']),"Balade")}
            {ir2("20h00","fa-solid fa-bed","#3b82f6",pp2(['Hébergement']),f"Nuit à {vil2}")}
          </div>
          <div class="itin-day">
            <div class="itin-hdr">{fi("fa-solid fa-cloud-sun","#fcd34d")} Jour 2 — Exploration</div>
            {ir2("09h30","fa-solid fa-gamepad","#ec4899",pp2(['Loisirs']),"Activité")}
            {ir2("11h00","fa-solid fa-chess-rook","#f59e0b",pp2(['Patrimoine'],1),"Patrimoine")}
            {ir2("13h00","fa-solid fa-basket-shopping","#16a34a","Marché","Produits locaux")}
            {ir2("15h00","fa-solid fa-person-hiking","#16a34a",pp2(['Nature'],1),"Nature")}
            {ir2("17h30","fa-solid fa-train","#3b82f6","Retour en train","Repartez ressourcé")}
          </div>
          <div class="eco-big" style="margin-top:1rem;">
            <div class="eco-num">{fi("fa-solid fa-leaf",ECO_NUM,"1.3rem")} −{co2_sv2} kg CO₂</div>
            <div class="eco-lbl">économisés sur l'aller-retour</div>
            <div style="font-size:.7rem;color:{ECO_LBL};margin-top:4px;">{fi("fa-solid fa-tree",ECO_LBL,"0.67rem")} {arbr2} arbre{'s' if arbr2>1 else ''}</div>
          </div>
        </div>""", unsafe_allow_html=True)
        pb1, pb2, pb3 = st.columns(3)
        with pb1:
            if st.button("Changer"): st.session_state.planner_step = 2; st.rerun()
        with pb2:
            if st.button("Enregistrer ce voyage", type="primary", use_container_width=True):
                if user: log_visit(user['id'], gk, co2_sv2, dist_km2); st.toast("Voyage enregistré !"); st.rerun()
                else: st.toast("Connectez-vous")
        with pb3:
            if st.button("Voir la destination", use_container_width=True):
                st.session_state.page = "destination"; st.rerun()

# ══════════════════════════════════════════════════════════════════
# PAGE : ÉCO-IMPACT
# ══════════════════════════════════════════════════════════════════
elif page == "eco":
    st.markdown(f"""<div style="background:linear-gradient(135deg,{'#021409,#042b16' if dk else '#d1fae5,#a7f3d0'});padding:2.5rem 2.5rem;text-align:center;border-bottom:1px solid {BORDER};">
      <div style="margin-bottom:9px;">{fi("fa-solid fa-leaf","#16a34a","1.8rem")}</div>
      <h1 style="color:{TEXT if not dk else '#d1fae5'};font-size:1.8rem;font-weight:900;margin:0;letter-spacing:-.04em;">Impact Écologique</h1>
      <p style="color:{TEXT2};margin-top:6px;font-size:.86rem;">Comparez vos émissions CO₂ selon le mode de transport</p>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="max-width:1440px;margin:0 auto;padding:2rem 2.5rem;">', unsafe_allow_html=True)
    e1, e2 = st.columns(2)
    with e1: dist = st.slider("Distance du trajet (km)", 30, 1500, 250, step=10)
    with e2: nbp = st.slider("Nombre de personnes", 1, 8, 1)

    CO2F = {"Train TER":2.4,"Bus":103,"Moto":191,"Voiture (seul)":218,"Voiture (2 pers.)":109,"Avion":258}
    vals = {k: round(v * dist * nbp / 1000, 2) for k, v in CO2F.items()}
    tr = vals["Train TER"]; vt = vals["Voiture (seul)"]
    eco = vt - tr; arbr = round(eco / 21, 1)

    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(f"""<div class="eco-big">
          <div class="eco-num">{tr:.1f}<span style="font-size:.8rem;"> kg</span></div>
          <div class="eco-lbl">{fi("fa-solid fa-train",ECO_LBL,"0.76rem")} Train TER · {dist} km</div>
        </div>""", unsafe_allow_html=True)
    with g2:
        st.markdown(f"""<div style="background:{'rgba(139,92,246,.1)' if dk else '#f5f3ff'};border:1px solid {'rgba(139,92,246,.25)' if dk else '#ddd6fe'};border-radius:16px;padding:1.6rem;text-align:center;">
          <div style="font-size:2.6rem;font-weight:900;color:#8b5cf6;letter-spacing:-.05em;">×{vt/max(tr,.01):.0f}</div>
          <div style="font-size:.8rem;color:#8b5cf6;margin-top:6px;">{fi("fa-solid fa-car","#8b5cf6","0.76rem")} La voiture pollue plus</div>
        </div>""", unsafe_allow_html=True)
    with g3:
        st.markdown(f"""<div class="eco-big">
          <div class="eco-num">−{eco:.1f}<span style="font-size:.8rem;"> kg</span></div>
          <div class="eco-lbl">{fi("fa-solid fa-arrows-left-right",ECO_LBL,"0.76rem")} Économisés vs voiture</div>
          <div style="font-size:.7rem;color:{ECO_LBL};margin-top:4px;">{fi("fa-solid fa-tree",ECO_LBL,"0.67rem")} {arbr} arbres</div>
        </div>""", unsafe_allow_html=True)

    CLRS = {"Train TER":"#16a34a","Bus":"#3b82f6","Moto":"#f59e0b","Voiture (seul)":"#ef4444","Voiture (2 pers.)":"#f97316","Avion":"#dc2626"}
    fig = go.Figure(go.Bar(x=list(vals.keys()), y=list(vals.values()),
        marker_color=[CLRS.get(k, "#6b7280") for k in vals],
        text=[f"{v:.1f} kg" for v in vals.values()], textposition="outside",
        textfont=dict(color=TEXT, size=11, family="Plus Jakarta Sans"),
        marker=dict(line=dict(width=0)), opacity=0.9))
    fig.update_layout(title=dict(text=f"CO₂ émis — {dist} km · {nbp} personne{'s' if nbp>1 else ''}",
        font=dict(color=TEXT, size=13)), height=290, showlegend=False,
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        yaxis=dict(showgrid=True, gridcolor=BORDER, color=TEXT2, zeroline=False),
        xaxis=dict(showgrid=False, color=TEXT2), margin=dict(l=0, r=0, t=38, b=0),
        font=dict(family="Plus Jakarta Sans"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""<div style="background:{'rgba(245,158,11,.08)' if dk else '#fefce8'};border-left:4px solid #f59e0b;border-radius:10px;padding:.9rem 1.2rem;margin-top:.5rem;">
      {fi("fa-solid fa-lightbulb","#f59e0b")} <b style="color:{TEXT};">Le saviez-vous ?</b>
      <span style="color:{TEXT2};font-size:.82rem;"> Si tous les Français prenaient le train pour les trajets courts, la France économiserait <b>12 millions de tonnes de CO₂ par an</b>.</span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PAGE : CARTE
# ══════════════════════════════════════════════════════════════════
elif page == "carte":
    st.markdown(f"""<div class="sect" style="padding-bottom:.5rem;">
      <div style="font-size:1.3rem;font-weight:800;color:{TEXT};letter-spacing:-.03em;margin-bottom:3px;">{fi("fa-solid fa-map-location-dot",BLUE,"0.95rem")} Carte interactive</div>
      <div style="font-size:.78rem;color:{TEXT2};margin-bottom:1rem;">Gares &amp; activités · Pays de la Loire</div>
    </div>""", unsafe_allow_html=True)
    mc1, mc2 = st.columns(2)
    with mc1: sg = st.checkbox("Gares SNCF", True, key="mg")
    with mc2: sp = st.checkbox("Points d'intérêt", True, key="mp")
    m_c = folium.Map(location=[47.2, -0.5], zoom_start=8, tiles=TILE)
    if sg:
        for _, g in df_dest.iterrows():
            sc__ = float(g.get('score_attractivite', 0) or 0)
            r_ = max(5, min(14, 5 + int(sc__)))
            folium.CircleMarker([g['latitude'], g['longitude']], radius=r_, color=BLUE, fill=True,
                fill_color=BLUE, fill_opacity=0.82, weight=2,
                popup=folium.Popup(f"<b>{str(g['nom_gare']).title()}</b><br>{sc__:.2f}/10", max_width=180),
                tooltip=str(g['nom_gare']).title()).add_to(m_c)
    if sp:
        with st.spinner("Chargement..."):
            df_pm = load_poi_map()
        cl_c = MarkerCluster(options={"maxClusterRadius": 45})
        for _, p in df_pm.iterrows():
            c = CAT_CLR.get(str(p.get('categorie', '')), '#6b7280')
            folium.CircleMarker([p['latitude'], p['longitude']], radius=5, color=c, fill=True,
                fill_opacity=0.82, weight=0,
                popup=f"<b>{p.get('nom','')}</b><br>{p.get('categorie','')}",
                tooltip=str(p.get('nom', ''))[:36]).add_to(cl_c)
        cl_c.add_to(m_c)
    st_folium(m_c, width=None, height=600, returned_objects=[])

# ══════════════════════════════════════════════════════════════════
# PAGE : PROFIL
# ══════════════════════════════════════════════════════════════════
elif page == "profil":
    if not user:
        st.warning("Connectez-vous pour accéder à votre profil.")
        st.stop()
    visits, favs, revs = get_user_stats(user['id'])
    nb_v = len(visits); co2_tot = float(visits['co2_saved_kg'].sum()) if nb_v > 0 else 0
    nb_f = len(favs); nb_r = len(revs); arbr_tot = round(co2_tot / 21, 1)
    initials = "".join([w[0].upper() for w in user['pseudo'].split()[:2]])

    st.markdown(f"""<div style="background:linear-gradient(135deg,{BLDARK},{BLUE});padding:2.5rem 2.5rem;text-align:center;">
      <div style="width:72px;height:72px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;
        justify-content:center;margin:0 auto 12px;font-size:1.6rem;font-weight:800;color:#fff;">{initials}</div>
      <h1 style="color:#fff;font-size:1.7rem;font-weight:900;margin:0;letter-spacing:-.03em;">{user['pseudo']}</h1>
      <div style="color:rgba(255,255,255,.6);font-size:.8rem;margin-top:5px;">
        {fi("fa-solid fa-location-dot","rgba(255,255,255,.6)","0.72rem")} {user['ville_depart']}
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="max-width:1440px;margin:0 auto;padding:2rem 2.5rem;">', unsafe_allow_html=True)
    p1, p2, p3, p4 = st.columns(4)
    for col, n, lbl, ico, c2 in [
        (p1, nb_v, "Voyages effectués", "fa-solid fa-train", BLUE),
        (p2, f"{co2_tot:.0f} kg", "CO₂ économisé", "fa-solid fa-leaf", GREEN),
        (p3, nb_f, "Destinations favorites", "fa-solid fa-heart", "#ec4899"),
        (p4, arbr_tot, "Arbres équivalents", "fa-solid fa-tree", "#16a34a"),
    ]:
        with col:
            st.markdown(f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:1.3rem;text-align:center;box-shadow:{SHADOW2};">
              <div style="font-size:2rem;font-weight:900;color:{c2};letter-spacing:-.05em;">{n}</div>
              <div style="font-size:.7rem;color:{TEXT2};margin-top:5px;">{fi(ico,TEXT2,'0.67rem')} {lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1.5rem 0 .8rem;letter-spacing:-.02em;'>{fi('fa-solid fa-trophy',ACCENT,'0.88rem')} Mes badges</div>", unsafe_allow_html=True)
    bcols = st.columns(7)
    for bi, b in enumerate(BADGES):
        unlocked = b['fn'](nb_v, co2_tot, nb_f)
        with bcols[bi]:
            st.markdown(f"""<div class="badge-card {'unlocked' if unlocked else 'locked'}">
              <div class="badge-ico" style="background:{b['bg']};">{fi(b['icon'],b['color'],'1.2rem')}</div>
              <div style="font-size:.7rem;font-weight:700;color:{TEXT};margin-bottom:2px;">{b['name']}</div>
              <div style="font-size:.62rem;color:{TEXT2};line-height:1.35;">{b['desc']}</div>
            </div>""", unsafe_allow_html=True)

    if nb_v > 0:
        st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1.5rem 0 .8rem;letter-spacing:-.02em;'>{fi('fa-solid fa-clock-rotate-left',BLUE,'0.88rem')} Mes voyages</div>", unsafe_allow_html=True)
        cols_show = [c for c in ['destination','co2_saved_kg','dist_km','visited_at'] if c in visits.columns]
        st.dataframe(visits[cols_show].rename(columns={
            'destination':'Destination','co2_saved_kg':'CO₂ économisé (kg)',
            'dist_km':'Distance (km)','visited_at':'Date'
        }), use_container_width=True, height=220)

    if nb_f > 0:
        st.markdown(f"<div style='font-size:1rem;font-weight:800;color:{TEXT};margin:1.5rem 0 .8rem;letter-spacing:-.02em;'>{fi('fa-solid fa-heart','#ec4899','0.88rem')} Mes favoris</div>", unsafe_allow_html=True)
        fv_cols = st.columns(min(4, nb_f))
        for fi_i, (_, frow) in enumerate(favs.head(8).iterrows()):
            dest_k = str(frow['destination'])
            fmeta = get_meta(dest_k)
            with fv_cols[fi_i % 4]:
                st.markdown(f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:11px;overflow:hidden;margin-bottom:.4rem;">
                  <div style="height:70px;background:{fmeta['grad']};position:relative;overflow:hidden;">
                    <img src="{fmeta['img']}" style="width:100%;height:100%;object-fit:cover;display:block;" loading="lazy">
                    <div style="position:absolute;inset:0;background:rgba(0,0,0,.35);"></div>
                    <div style="position:absolute;bottom:5px;left:8px;color:#fff;font-size:.75rem;font-weight:700;">{dest_k.title()}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────
st.markdown(f"""<div class="footer">
  <div style="font-size:.9rem;font-weight:800;color:rgba(255,255,255,.55);margin-bottom:.4rem;">TrainVoyage PDL</div>
  <div>Projet M1 Big Data &amp; IA · Tourisme en train · Pays de la Loire</div>
  <div style="margin-top:.3rem;color:rgba(255,255,255,.2);">Données SNCF Open Data · wttr.in · Picsum Photos</div>
</div>""", unsafe_allow_html=True)
