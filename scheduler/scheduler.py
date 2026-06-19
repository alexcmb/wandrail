import sys
import os
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)
log = logging.getLogger(__name__)

# ================================
# FONCTIONS DE MISE À JOUR
# ================================

def mise_a_jour_gares():
    log.info("🚉 Mise à jour des gares SNCF...")
    os.system("python scripts/01_gares.py")
    log.info("✅ Gares mises à jour !")

def mise_a_jour_poi():
    log.info("🏨 Mise à jour des POI...")
    os.system("python scripts/02_datatourisme.py")
    os.system("python scripts/04_enrichissement.py")
    log.info("✅ POI mis à jour !")

def mise_a_jour_mobilites():
    log.info("🚲 Mise à jour mobilités...")
    os.system("python scripts/03_mobilites.py")
    log.info("✅ Mobilités mises à jour !")

# ================================
# PLANIFICATION
# ================================
scheduler = BlockingScheduler()

# Gares : chaque lundi à 2h
scheduler.add_job(
    mise_a_jour_gares,
    'cron',
    day_of_week='mon',
    hour=2,
    minute=0,
    name='MAJ Gares'
)

# POI : chaque dimanche à 3h
scheduler.add_job(
    mise_a_jour_poi,
    'cron',
    day_of_week='sun',
    hour=3,
    minute=0,
    name='MAJ POI'
)

# Mobilités : toutes les heures
scheduler.add_job(
    mise_a_jour_mobilites,
    'interval',
    hours=1,
    name='MAJ Mobilités'
)

log.info("=" * 50)
log.info("🚀 Scheduler démarré !")
log.info("📅 Gares : chaque lundi à 2h")
log.info("📅 POI : chaque dimanche à 3h")
log.info("📅 Mobilités : toutes les heures")
log.info("=" * 50)

# Première mise à jour au démarrage
mise_a_jour_mobilites()

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    log.info("⛔ Scheduler arrêté")