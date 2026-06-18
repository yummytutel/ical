from icalendar import Calendar
import requests
import os

# === CONFIGURATION ===
# URL du calendrier source (.ics)
SOURCE_URL = "https://cerfal.ymag.cloud/index.php/planning/ical/4C5147AA-B18B-4694-A195-F5214220B11F/"  
# Texte à filtrer (événements contenant ce texte dans le titre seront supprimés)
EVENT_TO_REMOVE = "Entreprise"            
# Dossier et nom du fichier de sortie
OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "filtré.ics")

# === CODE ===
print("Téléchargement du calendrier source...")
response = requests.get(SOURCE_URL)
response.raise_for_status()

# Charger le calendrier d'origine
cal = Calendar.from_ical(response.content)

# Créer un nouveau calendrier
filtered_cal = Calendar()

# Copier les métadonnées du calendrier (titre, prodid, etc.)
for key, value in cal.items():
    filtered_cal.add(key, value)

# S'assurer que le dossier docs/ existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Compter les événements supprimés
count_removed = 0
count_kept = 0

# Parcourir les événements et filtrer
for component in cal.walk():
    if component.name == "VEVENT":
        summary = str(component.get("summary", ""))
        if EVENT_TO_REMOVE.lower() in summary.lower():
            count_removed += 1
        else:
            filtered_cal.add_component(component)
            count_kept += 1
    else:
        # Conserver les autres composants (VTIMEZONE, etc.)
        if component.name != "VCALENDAR":
            filtered_cal.add_component(component)

# Sauvegarder le fichier final
with open(OUTPUT_FILE, "wb") as f:
    f.write(filtered_cal.to_ical())

print(f" Calendrier filtré enregistré dans {OUTPUT_FILE}")
print(f" {count_kept} événements gardés,  {count_removed} supprimés.")
