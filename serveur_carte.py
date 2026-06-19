"""
Mini serveur HTTP local pour afficher la carte dans Power BI
Lancer ce script AVANT d'ouvrir Power BI
"""
import http.server
import socketserver
import os
import threading
import webbrowser

PORT = 8765
DOSSIER = r"C:\Users\thili\Desktop\tourisme_train"

os.chdir(DOSSIER)

handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"✅ Serveur démarré sur http://localhost:{PORT}")
    print(f"🗺️  Carte accessible sur : http://localhost:{PORT}/carte_interactive.html")
    print(f"\n⚠️  Laisse cette fenêtre ouverte tant que Power BI est ouvert !")
    print(f"   (Ctrl+C pour arrêter)\n")
    httpd.serve_forever()
