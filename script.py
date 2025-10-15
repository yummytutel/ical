
from icalendar import Calendar
import requests

# URL du calendrier d'origine
SOURCE_URL = "https://cerfal.ymag.cloud/index.php/planning/ical/4C5147AA-B18B-4694-A195-F5214220B11F/"
# Nom de l'événement à filtrer
EVENT_TO_REMOVE = "Entreprise"
# Fichier de sortie
OUTPUT_FILE = "filtré.ics"

# Télécharger le calendrier source
response = requests.get(SOURCE_URL)
response.raise_for_status()

# Charger le calendrier
cal = Calendar.from_ical(response.content)

# Nouveau calendrier filtré
filtered_cal = Calendar()
for key, value in cal.items():
    filtered_cal.add(key, value)

# Garder seulement les événements qui ne contiennent PAS le texte interdit
for component in cal.walk():
    if component.name == "VEVENT":
        summary = str(component.get("summary", ""))
        if EVENT_TO_REMOVE.lower() not in summary.lower():
            filtered_cal.add_component(component)

# Sauvegarder le résultat
with open(OUTPUT_FILE, "wb") as f:
    f.write(filtered_cal.to_ical())

print(f"Calendrier filtré enregistré dans {OUTPUT_FILE}")
