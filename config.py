"""Ustawienia termometru.

Wszystko, co można chcieć zmienić bez dotykania logiki programu, jest tutaj.
Tajne dane (token GitHuba) NIE są zapisane w kodzie: czytamy je ze zmiennej
środowiskowej GITHUB_TOKEN albo z pliku .env obok tego pliku.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env_file(path: Path) -> None:
    """Wczytuje proste linie KLUCZ=WARTOŚĆ z pliku .env (jeśli istnieje).

    Zmienne ustawione już w środowisku mają pierwszeństwo.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_env_file(BASE_DIR / ".env")

# --- Paski LED ---------------------------------------------------------------
LED_COUNT_EXT = 61               # diody skali temperatury zewnętrznej
LED_COUNT_INT = 21               # diody skali temperatury w domu
LED_COUNT = LED_COUNT_EXT + LED_COUNT_INT
LED_PIN = 18                     # GPIO 18 (PWM)
LED_FREQ_HZ = 800000             # częstotliwość sygnału
LED_DMA = 10                     # kanał DMA
LED_BRIGHTNESS = 20              # 0 = najciemniej, 255 = najjaśniej
LED_INVERT = False               # True przy tranzystorze NPN
LED_CHANNEL = 0                  # 1 dla GPIO 13, 19, 41, 45, 53

# Temperatura, od której zapala się PIERWSZA dioda danej skali.
EXT_MIN_TEMP = -20               # skala zewnętrzna: -20 ... +40 °C
INT_MIN_TEMP = 10                # skala domowa:      10 ...  30 °C

# --- Czasy (sekundy) ---------------------------------------------------------
PIXEL_DELAY_S = 0.05             # opóźnienie między kolejnymi diodami w animacji
LOOP_PAUSE_S = 10                # przerwa po narysowaniu temperatur
RESTART_DELAY_S = 5              # przerwa przed ponowną próbą po błędzie
PUBLISH_EVERY_N_LOOPS = 8        # co ile pętli wysyłamy dane na GitHub

# --- Efekty przy odświeżaniu --------------------------------------------------
# Na początku wyświetlania (jak pojawiają się nowe temperatury).
# Dostępne: "fill" (klasyczne wypełnianie dioda po diodzie), "drop" (krople spadają i układają się w słupek),
#           "twinkle" (diody pojawiają się losowo z białym błyskiem), "comet" (kometa
#           zostawia za sobą obraz), "rainbow" (tęcza zamienia się w obraz),
#           "curtain" (obraz otwiera się od końców paska ku środkowi).
# "random" = losuje z listy INTROS_ENABLED (bez powtarzania tego samego dwa razy z rzędu).
INTRO = "random"
INTROS_ENABLED = ["fill", "drop", "twinkle", "comet", "rainbow", "curtain"]

# Na końcu wyświetlania: efekt, którym gaśnie stary obraz, zanim narysują się nowe temperatury.
# Dostępne: "fade" (płynne wygaszenie), "dissolve" (losowe gaśnięcie diod),
#           "comet" (kometa zmiatająca obraz), "rainbow" (tęcza, potem wygaszenie),
#           "curtain" (zamykanie od końców paska), "clear" (zgaszenie od razu).
# "random" = losuje z listy TRANSITIONS_ENABLED (bez powtarzania tego samego dwa razy z rzędu).
TRANSITION = "random"
TRANSITIONS_ENABLED = ["fade", "dissolve", "comet", "rainbow", "curtain"]
TRANSITION_PAUSE_S = 0.5         # przerwa w ciemności po przejściu, przed rysowaniem

# --- Czujnik w salonie: Aqara (Zigbee2MQTT, odczyt z journalctl) --------------
ZIGBEE_SERVICE = "zigbee2mqtt.service"
ZIGBEE_JOURNAL_LINES = 200       # ile ostatnich linii dziennika przeszukać
ZIGBEE_DEVICE_ID = None          # np. "0x00158d0007f00fc5"; None = ostatni odczyt dowolnego czujnika
INDOOR_ROOM_NAME = "salon"       # odczyty Aqara trafiają do temperatures_salon.txt (razem z temperatures.txt)

# --- GitHub ------------------------------------------------------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "witoldaksamit-ui/velvethome.github.io"
GITHUB_BRANCH = "main"
TEMPERATURES_FILE = "temperatures.txt"   # historia pomiarów (czytana m.in. przez aplikację)
GARMIN_FILE = "monkey.txt"               # ostatni odczyt (3 linie, czytany przez zegarek)
TEMPERATURES_MAX_LINES = 800             # starsze linie są obcinane
TIMEZONE = "Europe/Warsaw"               # strefa czasowa znaczników w temperatures.txt

# --- Czujniki Tuya (temperatura i wilgotność, przez chmurę Tuya) --------------
# Klucze projektu z iot.tuya.com (apiRegion, apiKey, apiSecret). Plik jest w .gitignore.
TUYA_CONFIG_FILE = BASE_DIR / "tinytuya.json"
# nazwa -> identyfikator urządzenia; nazwa trafia do nazwy pliku temperatures_<nazwa>.txt
# Pusty słownik ({}) wyłącza odczyt czujników Tuya.
TUYA_DEVICES = {
    "pralnia": "bf22a8ae0e7d2f7e99w8oz",
    "dwor": "bf6f151e6964c9f11btvp3",        # czujnik za oknem (wcześniej zapisywany jako "sypialnia")
    "sypialnia": "bfaf966b02038b62f8cqik",   # czujnik w sypialni
}
# Jednorazowe przeniesienie historii przy starcie: (stara nazwa, nowa nazwa). Gdy plik nowej nazwy
# już istnieje na GitHubie, nic się nie dzieje. Stary plik jest czyszczony, żeby nie mieszać danych.
TUYA_FILE_MIGRATIONS = [("sypialnia", "dwor")]
# Osuszacz Warmtec ODT-12N Wi-Fi w pralni (odczyt co TUYA_INTERVAL_S razem z czujnikami); None wyłącza
DEHUMIDIFIER_ID = "1401128048e729763e64"
DEHUMIDIFIER_FILE = "osuszacz.txt"
# Sterownik pieca ENGO E901 Wi-Fi (odczyt co TUYA_INTERVAL_S); None wyłącza
THERMOSTAT_ID = "bf0794cb06d981061dzhno"
THERMOSTAT_FILE = "piec.txt"   # linia: <czas>,<temp.>,<nastawa>,<grzeje 1/0>,<tryb>,<bateria>,<łączność 1/0>,<błędy>,<włączony 1/0>   # linia: <czas>,<włączony 1/0>,<tryb>,<cel %>,<wentylator>,<wilgotność %>,<błędy>
TUYA_INTERVAL_S = 300                    # najczęściej co tyle sekund pytamy chmurę Tuya
TUYA_FILE_PATTERN = "temperatures_{name}.txt"   # linia: <czas ISO, Warszawa>,<temperatura>,<wilgotność>
TUYA_HISTORY_HOURS = 24                  # starsze linie są obcinane

# --- Źródło temperatury zewnętrznej (LED, temperatures.txt, monkey.txt) -------
OUTDOOR_TUYA_SENSOR = "dwor"             # nazwa z TUYA_DEVICES
OUTDOOR_MAX_AGE_S = 900                  # starszy odczyt Tuya: ostrzeżenie w logu (zostaje ostatnia wartość)
