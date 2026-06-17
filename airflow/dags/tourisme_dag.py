"""
DAG Airflow - Pipeline Wandrail (Pays de la Loire)
Architecture Medaillon : Bronze -> Silver -> Gold -> ML
Execution : chaque semaine (dimanche a 2h du matin)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import os


default_args = {
    "owner"      : "wandrail",
    "retries"    : 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

dag = DAG(
    "wandrail_pipeline",
    default_args=default_args,
    description="Pipeline Medaillon Wandrail - Bronze -> Silver -> Gold -> ML",
    schedule_interval="0 2 * * 0",  # Chaque dimanche a 2h
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["wandrail", "sncf", "medaillon", "ml"],
)


def run_script(script_name: str):
    """Lance un script Python depuis le dossier scripts/ avec gestion d'erreur."""
    script_path = f"/opt/airflow/scripts/{script_name}"
    env         = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        ["python", script_path],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"Script {script_name} a echoue :\n{result.stderr}")


# Definition des taches
t0  = PythonOperator(task_id="init_database",          python_callable=lambda: run_script("00_init_db.py"),    dag=dag)
t1  = PythonOperator(task_id="extract_gares",          python_callable=lambda: run_script("01_gares.py"),      dag=dag)
t2  = PythonOperator(task_id="extract_poi_datatourisme",python_callable=lambda: run_script("02_datatourisme.py"), dag=dag)
t3  = PythonOperator(task_id="extract_osm",            python_callable=lambda: run_script("03_osm.py"),        dag=dag)
t4  = PythonOperator(task_id="enrichissement_silver",  python_callable=lambda: run_script("04_enrichissement.py"), dag=dag)
t5  = PythonOperator(task_id="gold_layer",             python_callable=lambda: run_script("05_gold_layer.py"), dag=dag)
t6  = PythonOperator(task_id="ml_clustering",          python_callable=lambda: run_script("06_ml_clustering.py"), dag=dag)
t7  = PythonOperator(task_id="ml_recommandation",      python_callable=lambda: run_script("07_ml_recommandation.py"), dag=dag)
t8  = PythonOperator(task_id="isochrones_navitia",     python_callable=lambda: run_script("08_navitia.py"),    dag=dag)
t9  = PythonOperator(task_id="evenements_openagenda",  python_callable=lambda: run_script("09_evenements.py"), dag=dag)
t10 = PythonOperator(task_id="population_insee",       python_callable=lambda: run_script("10_insee.py"),      dag=dag)


# ----------------------------------------------------------
# Ordre d'execution
#
#  t0 (init DB)
#    |
#  t1 (gares) ----+
#  t2 (POI DT) ---+---> t4 (enrichissement Silver)
#  t3 (OSM) ------+              |
#  t9 (events)                   v
#  t10 (INSEE)              t5 (Gold layer)
#                           /           \
#                    t6 (KMeans)     t7 (KNN)
#                                    t8 (Navitia)
# ----------------------------------------------------------

t0 >> [t1, t2, t3, t9, t10] >> t4 >> t5 >> [t6, t7, t8]
