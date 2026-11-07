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
# Dostępne: "fill" (klasyczne wypełnianie dioda po diodzie), "fade" (płynne rozjaśnienie),
#           "twinkle" (diody pojawiają się losowo z białym błyskiem), "comet" (kometa
#           zostawia za sobą obraz), "rainbow" (tęcza zamienia się w obraz),
#           "curtain" (obraz otwiera się od końców paska ku środkowi).
# "random" = losuje z listy INTROS_ENABLED (bez powtarzania tego samego dwa razy z rzędu).
INTRO = "random"
INTROS_ENABLED = ["fill", "fade", "twinkle", "comet", "rainbow", "curtain"]

# Na końcu wyświetlania: efekt, którym gaśnie stary obraz, zanim narysują się nowe temperatury.
# Dostępne: "fade" (płynne wygaszenie), "dissolve" (losowe gaśnięcie diod),
#           "comet" (kometa zmiatająca obraz), "rainbow" (tęcza, potem wygaszenie),
#           "curtain" (zamykanie od końców paska), "clear" (zgaszenie od razu).
# "random" = losuje z listy TRANSITIONS_ENABLED (bez powtarzania tego samego dwa razy z rzędu).
TRANSITION = "random"
TRANSITIONS_ENABLED = ["fade", "dissolve", "comet", "rainbow", "curtain"]
TRANSITION_PAUSE_S = 0.5         # przerwa w ciemności po przejściu, przed rysowaniem

# --- Czujnik zewnętrzny (Zigbee2MQTT, odczyt z journalctl) --------------------
ZIGBEE_SERVICE = "zigbee2mqtt.service"
ZIGBEE_JOURNAL_LINES = 200       # ile ostatnich linii dziennika przeszukać
ZIGBEE_DEVICE_ID = None          # np. "0x00158d0007f00fc5"; None = pierwszy z brzegu

# --- GitHub ------------------------------------------------------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "witoldaksamit-ui/velvethome.github.io"
GITHUB_BRANCH = "main"
TEMPERATURES_FILE = "temperatures.txt"   # historia pomiarów (czytana m.in. przez aplikację)
GARMIN_FILE = "monkey.txt"               # ostatni odczyt (3 linie, czytany przez zegarek)
TEMPERATURES_MAX_LINES = 800             # starsze linie są obcinane
TIMEZONE = "Europe/Warsaw"               # strefa czasowa znaczników w temperatures.txt
