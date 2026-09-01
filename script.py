from icalendar import Calendar
import requests
import os
from datetime import datetime, date

# === CONFIGURATION ===
# URL du calendrier source (.ics)
SOURCE_URL = "https://cerfal.ymag.cloud/index.php/planning/ical/4C5147AA-B18B-4694-A195-F5214220B11F/"
# Texte à filtrer (événements contenant ce texte dans le titre seront supprimés)
EVENT_TO_REMOVE = "Entreprise"
# Dossier et nom du fichier de sortie
OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "filtré.ics")

# Heure à partir de laquelle un événement est considéré comme "après-midi"
AFTERNOON_START_HOUR = 12

# Les événements d'après-midi ne sont supprimés QUE s'ils ont lieu avant cette date
# (à ajuster si besoin : ici le 1er novembre 2026)
CUTOFF_DATE = date(2026, 11, 1)

# Sur les mercredis "hors entreprise" (pas de rendez-vous "Entreprise" ce jour-là),
# on garde l'après-midi une semaine sur deux, en partant du plus ancien mercredi
# concerné. Mettre à False pour garder plutôt le 2e, 4e, 6e... mercredi.
KEEP_FIRST_ALTERNATE_WEDNESDAY = True

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


def get_event_date(component):
    """Retourne la date (sans l'heure) de début d'un événement, ou None."""
    dtstart = component.get("dtstart")
    if dtstart is None:
        return None
    value = dtstart.dt
    if isinstance(value, datetime):
        return value.date()
    return value  # événement journée entière : déjà une date


def is_afternoon(component):
    """True si l'événement a une heure de début et qu'elle tombe l'après-midi."""
    dtstart = component.get("dtstart")
    if dtstart is None:
        return False
    value = dtstart.dt
    if not isinstance(value, datetime):
        return False  # événement journée entière, pas d'horaire -> non concerné
    return value.hour >= AFTERNOON_START_HOUR


def is_entreprise(component):
    summary = str(component.get("summary", ""))
    return EVENT_TO_REMOVE.lower() in summary.lower()


vevents = [c for c in cal.walk() if c.name == "VEVENT"]

# 1er passage : repérer les dates marquées "Entreprise"
entreprise_dates = set()
for component in vevents:
    if is_entreprise(component):
        d = get_event_date(component)
        if d is not None:
            entreprise_dates.add(d)

# 2e passage : lister les mercredis "hors entreprise" avant la date limite, triés
free_wednesdays = sorted({
    d for c in vevents
    for d in [get_event_date(c)]
    if d is not None
    and d.weekday() == 2  # 0 = lundi ... 2 = mercredi
    and d < CUTOFF_DATE
    and d not in entreprise_dates
})
kept_wednesdays = set(
    free_wednesdays[0::2] if KEEP_FIRST_ALTERNATE_WEDNESDAY else free_wednesdays[1::2]
)

# Compter les événements supprimés / gardés
count_removed = 0
count_kept = 0

# Parcourir les événements et filtrer
for component in cal.walk():
    if component.name == "VEVENT":
        if is_entreprise(component):
            count_removed += 1
            continue

        d = get_event_date(component)
        if d is not None and d < CUTOFF_DATE and is_afternoon(component):
            if d.weekday() == 2 and d in kept_wednesdays:
                # Mercredi "hors entreprise" gardé (1 sur 2)
                filtered_cal.add_component(component)
                count_kept += 1
            else:
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

print(f"Calendrier filtré enregistré dans {OUTPUT_FILE}")
print(f"{count_kept} événements gardés, {count_removed} supprimés.")
