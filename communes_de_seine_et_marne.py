# Carte des communes de Seine-et-Marne - correction erreur 403 OpenStreetMap
#
# PROBLEME : depuis 2026, les serveurs de tuiles d'OpenStreetMap exigent un
# en-tete HTTP "Referer". Ouvrir le HTML en local (file://) n'envoie jamais
# de Referer -> erreur "403 Access blocked - Referer is required".
#
# SOLUTION definitive : servir la carte via un petit serveur HTTP local.
# En http://localhost, le navigateur envoie automatiquement un Referer
# valide et OpenStreetMap accepte les tuiles.
#
# UTILISATION :
#   python carte_communes_77.py            # genere la carte + lance le serveur + ouvre le navigateur
#   python carte_communes_77.py --no-serve # genere seulement le fichier HTML

import os
import sys
import threading
import time
import webbrowser

import folium

# Coordonnees des communes (WGS84, centre-bourg / mairie)
cities = {
    "Champs-sur-Marne": [48.885, 2.603],
    "Melun": [48.540, 2.660],
    "Dammarie-les-Lys": [48.517, 2.644],
    "Nemours": [48.267, 2.700],
    "Chelles": [48.878, 2.593],
    "Provins": [48.560, 3.299],
    "Bussy-Saint-Georges": [48.843, 2.702],
    "Mary-sur-Marne": [49.014, 3.029],
    "Mitry-Mory": [48.982, 2.619],
    "Lieusaint": [48.628, 2.567],
    "Meaux": [48.956, 2.889],
    "Roissy-en-Brie": [48.796, 2.655],
    "Vaires-sur-Marne": [48.878, 2.713],
    "Montereau-Fault-Yonne": [48.382, 2.955],
    "Léchelle": [48.577, 3.391],
    "Vaux-le-Pénil": [48.533, 2.687],
    "Montry": [48.888, 2.828],
    "Pontault-Combault": [48.806, 2.606],
    "Moissy-Cramayel": [48.627, 2.596],
    "Nangis": [48.553, 3.027],
    "Fontenay-Trésigny": [48.708, 2.864],
    "Guignes": [48.637, 2.798],
    "Noisiel": [48.848, 2.617],
    "Jouarre": [48.934, 3.133],
    "Savins": [48.511, 3.201],
    "Nanteuil-sur-Marne": [48.981, 3.220],
}

# Communes d'anciens elus (marqueurs verts)
former_officials_cities = {
    "Courtry": [48.910, 2.584],
    "Lagny-sur-Marne": [48.878, 2.674],
    "Le Pin": [48.914, 2.630],
    "Mitry-Mory": [48.982, 2.619],
}

# Communes en bleu
blue_cities = {

}

OUTPUT_FILE = "communes_seine_et_marne.html"
PORT = 8000


def build_map():
    m = folium.Map(location=[48.64, 2.63], zoom_start=10)

    # Fond OpenStreetMap standard, autorise par la politique OSMF
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap",
    ).add_to(m)

    # Discernement : empeche l'indexation de la page par les moteurs de
    # recherche (Google, Bing...). La carte reste accessible a qui possede
    # l'URL, mais n'apparait dans aucun resultat de recherche.
    m.get_root().html.add_child(
        folium.Element('<meta name="robots" content="noindex, nofollow">')
    )

    # Contour du departement de Seine-et-Marne (source : france-geojson,
    # donnees IGN, domaine public). Le telechargement se fait a la
    # generation ; si vous generevez la carte sans internet, le contour
    # est simplement omis (la carte et les marqueurs restent fonctionnels).
    try:
        import urllib.request

        geojson_url = (
            "https://raw.githubusercontent.com/gregoiredavid/france-geojson/"
            "master/departements/77-seine-et-marne/"
            "departement-77-seine-et-marne.geojson"
        )
        with urllib.request.urlopen(geojson_url, timeout=15) as response:
            import json

            sm_geojson = json.loads(response.read().decode("utf-8"))

        folium.GeoJson(
            sm_geojson,
            name="Seine-et-Marne",
            style_function=lambda feature: {
                "fillColor": "transparent",
                "color": "#2b6cb0",   # couleur du trait
                "weight": 2,          # epaisseur du trait
                "fillOpacity": 0,
            },
            tooltip="Seine-et-Marne (77)",
        ).add_to(m)
        print("Contour de la Seine-et-Marne ajoute.")
    except Exception as e:
        print(f"Contour du departement non ajoute ({e}).")

    for city, coords in cities.items():
        folium.Marker(
            location=coords,
            popup=city,
            tooltip=city,
        ).add_to(m)

    # Anciens elus : marqueurs verts
    for city, coords in former_officials_cities.items():
        folium.Marker(
            location=coords,
            popup=city,
            tooltip=f"{city} (ancien.ne elu.e)",
            icon=folium.Icon(color="green"),
        ).add_to(m)

    # Communes en bleu
    for city, coords in blue_cities.items():
        folium.Marker(
            location=coords,
            popup=city,
            tooltip=city,
            icon=folium.Icon(color="blue"),
        ).add_to(m)

    m.save(OUTPUT_FILE)
    print(f"Carte generee : {os.path.abspath(OUTPUT_FILE)}")


def serve_and_open():
    """Sert le dossier courant en HTTP local et ouvre la carte.

    Servi en http://localhost, le navigateur envoie un Referer valide :
    OpenStreetMap ne bloque plus les tuiles (plus d'erreur 403).
    """
    import http.server
    import socketserver

    directory = os.path.dirname(os.path.abspath(OUTPUT_FILE))
    os.chdir(directory)

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/{OUTPUT_FILE}"
        print(f"Serveur local demarre sur {url}")
        print("Appuyez sur Ctrl+C pour arreter le serveur.")
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrete.")


if __name__ == "__main__":
    build_map()
    if "--no-serve" in sys.argv:
        print("Fichier genere. Ouvrez-le via un serveur local pour eviter le 403 :")
        print(f"  python -m http.server {PORT}  puis  http://localhost:{PORT}/{OUTPUT_FILE}")
    else:
        serve_and_open()