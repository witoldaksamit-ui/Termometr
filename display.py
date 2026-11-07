"""Obsługa pasków LED: skale temperatury oraz efekty na początku i na końcu wyświetlania."""

import logging
import random
import time
from typing import Callable, Dict, List, Optional

from rpi_ws281x import Adafruit_NeoPixel, Color

import config
from colors import COLORS_EXT, COLORS_INT

log = logging.getLogger(__name__)

OFF = 0x000000


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def lit_count(temperature: int, min_temp: int, led_count: int) -> int:
    """Ile diod ma się zaświecić dla danej temperatury (0 ... led_count).

    Pierwsza dioda zapala się przy min_temp, każdy kolejny stopień dokłada jedną.
    Wartości spoza skali są obcinane, więc upał ani mróz nie psują programu.
    """
    return _clamp(temperature - min_temp + 1, 0, led_count)


def wheel(pos: int) -> int:
    """Kolor tęczy dla pozycji 0-255 (czerwony -> zielony -> niebieski -> czerwony)."""
    pos %= 256
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    if pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    pos -= 170
    return Color(0, pos * 3, 255 - pos * 3)


def scale_color(color: int, factor: float) -> int:
    """Przyciemnia kolor (factor 0.0 = czarny, 1.0 = bez zmian)."""
    r, g, b = (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF
    return Color(int(r * factor), int(g * factor), int(b * factor))


class LedDisplay:
    def __init__(self) -> None:
        self.strip = Adafruit_NeoPixel(
            config.LED_COUNT,
            config.LED_PIN,
            config.LED_FREQ_HZ,
            config.LED_DMA,
            config.LED_INVERT,
            config.LED_BRIGHTNESS,
            config.LED_CHANNEL,
        )
        self.strip.begin()
        self._frame: List[int] = [OFF] * config.LED_COUNT  # to, co aktualnie świeci
        self._last_transition: Optional[str] = None
        self._last_intro: Optional[str] = None

        # Efekty na KOŃCU wyświetlania: gaszą stary obraz.
        self._transitions: Dict[str, Callable[[], None]] = {
            "clear": self.clear,
            "fade": self._fade_out,
            "dissolve": self._dissolve,
            "comet": self._comet,
            "rainbow": self._rainbow_out,
            "curtain": self._curtain,
        }
        # Efekty na POCZĄTKU wyświetlania: budują nowy obraz (argument = docelowa ramka).
        self._intros: Dict[str, Callable[[List[int]], None]] = {
            "fill": self._intro_fill,
            "drop": self._intro_drop,
            "twinkle": self._intro_twinkle,
            "comet": self._comet,
            "rainbow": self._intro_rainbow,
            "curtain": self._curtain,
        }

    # --- podstawowe operacje ---------------------------------------------------
    def _set(self, index: int, color: int) -> None:
        self.strip.setPixelColor(index, color)
        self._frame[index] = color

    def clear(self) -> None:
        """Gasi wszystkie diody naraz."""
        for i in range(self.strip.numPixels()):
            self._set(i, OFF)
        self.strip.show()

    def wipe(self, color: int, wait_s: float = 0.05) -> None:
        """Zapala (lub gasi, dla koloru 0) kolejne diody jedna po drugiej."""
        for i in range(self.strip.numPixels()):
            self._set(i, color)
            self.strip.show()
            time.sleep(wait_s)

    def turn_off(self) -> None:
        self.wipe(Color(0, 0, 0), 0.01)

    def _apply(self, frame: List[int]) -> None:
        """Ustawia dokładnie podany obraz."""
        for i, color in enumerate(frame):
            self._set(i, color)
        self.strip.show()

    def _pick_effect(self, requested: str, enabled, registry, last: Optional[str], fallback: str) -> str:
        """Wybiera efekt: konkretny, albo losowy z listy (bez powtórzenia poprzedniego)."""
        name = requested
        if name == "random":
            choices = [n for n in enabled if n in registry]
            if len(choices) > 1 and last in choices:
                choices.remove(last)
            name = random.choice(choices) if choices else fallback
        if name not in registry:
            log.warning("Nieznany efekt '%s', używam '%s'", name, fallback)
            name = fallback
        return name

    # --- skale temperatury -----------------------------------------------------
    def target_frame(self, outdoor: int, indoor: int) -> List[int]:
        """Docelowy obraz dla podanych temperatur (kolor albo zgaszona dioda dla każdej diody)."""
        lit_ext = lit_count(outdoor, config.EXT_MIN_TEMP, config.LED_COUNT_EXT)
        lit_int = lit_count(indoor, config.INT_MIN_TEMP, config.LED_COUNT_INT)
        frame = [OFF] * config.LED_COUNT
        for i, color in enumerate(COLORS_EXT):
            frame[i] = color if i < lit_ext else OFF
        for i, color in enumerate(COLORS_INT):
            frame[config.LED_COUNT_EXT + i] = color if i < lit_int else OFF
        return frame

    def show_temps(self, outdoor: int, indoor: int, intro: Optional[str] = None) -> None:
        """Rysuje obie skale (zewnętrzną od diody 0, domową zaraz po niej) wybranym efektem."""
        target = self.target_frame(outdoor, indoor)
        name = self._pick_effect(
            intro or config.INTRO, config.INTROS_ENABLED, self._intros, self._last_intro, "fill"
        )
        self._last_intro = name
        self._intros[name](target)
        self._apply(target)  # gwarancja, że na końcu świeci dokładnie to, co trzeba

    def show_palette(self) -> None:
        """Test: zapala obie skale w pełnych kolorach."""
        for i, color in enumerate(COLORS_EXT):
            self._set(i, color)
            self.strip.show()
            time.sleep(0.01)
        for i, color in enumerate(COLORS_INT):
            self._set(config.LED_COUNT_EXT + i, color)
            self.strip.show()
            time.sleep(0.03)

    # --- koniec wyświetlania: gaszenie starego obrazu ----------------------------
    def transition(self, name: Optional[str] = None) -> None:
        """Gasi aktualny obraz wybranym efektem, a potem robi krótką przerwę w ciemności."""
        name = self._pick_effect(
            name or config.TRANSITION,
            config.TRANSITIONS_ENABLED,
            self._transitions,
            self._last_transition,
            "clear",
        )
        self._last_transition = name
        self._transitions[name]()
        self.clear()  # gwarancja, że pasek jest całkiem zgaszony
        time.sleep(config.TRANSITION_PAUSE_S)

    def _fade_out(self, steps: int = 25, delay: float = 0.04) -> None:
        """Płynne wygaszanie całego obrazu."""
        start = list(self._frame)
        if not any(start):
            return
        for step in range(steps - 1, -1, -1):
            factor = (step / steps) ** 2  # kwadrat = wygaszanie wygląda równomiernie dla oka
            for i, color in enumerate(start):
                self._set(i, scale_color(color, factor))
            self.strip.show()
            time.sleep(delay)

    def _dissolve(self, duration: float = 1.5) -> None:
        """Diody gasną w losowej kolejności (rozpuszczanie)."""
        lit = [i for i, color in enumerate(self._frame) if color != OFF]
        if not lit:
            return
        random.shuffle(lit)
        delay = duration / len(lit)
        for i in lit:
            self._set(i, OFF)
            self.strip.show()
            time.sleep(delay)

    def _rainbow_out(self, duration: float = 1.5, fps: int = 50) -> None:
        """Tęcza przesuwa się po całym pasku, a potem płynnie gaśnie."""
        n = self.strip.numPixels()
        for frame in range(int(duration * fps)):
            for i in range(n):
                self._set(i, wheel(i * 256 // n + frame * 8))
            self.strip.show()
            time.sleep(1 / fps)
        self._fade_out()

    # --- efekty działające w obie strony ----------------------------------------
    # behind = obraz, który zostaje ZA efektem: None = zgaszony pasek (gaszenie),
    # lista kolorów = docelowy obraz (budowanie).
    def _comet(self, behind: Optional[List[int]] = None, tail: int = 8, delay: float = 0.015) -> None:
        """Kolorowa kometa z ogonem przebiega przez pasek; za nią zostaje obraz `behind`."""
        n = self.strip.numPixels()
        behind = behind or [OFF] * n
        hue = random.randrange(256)
        for pos in range(n + tail):
            for k in range(tail):
                index = pos - k
                if 0 <= index < n:
                    factor = 1.0 if k == 0 else (1 - k / tail) ** 2
                    self._set(index, scale_color(wheel(hue + k * 6), factor))
            settled = pos - tail
            if 0 <= settled < n:
                self._set(settled, behind[settled])
            self.strip.show()
            time.sleep(delay)

    def _curtain(self, behind: Optional[List[int]] = None, delay: float = 0.03) -> None:
        """Dwa kolorowe światełka biegną od końców paska ku środkowi; za nimi zostaje obraz `behind`."""
        n = self.strip.numPixels()
        behind = behind or [OFF] * n
        last = (n + 1) // 2 - 1
        for k in range(last + 1):
            left, right = k, n - 1 - k
            color = wheel(k * 6)
            self._set(left, color)
            self._set(right, color)
            if k > 0:
                self._set(left - 1, behind[left - 1])
                self._set(right + 1, behind[right + 1])
            self.strip.show()
            time.sleep(delay)
        self._set(last, behind[last])
        self._set(n - 1 - last, behind[n - 1 - last])
        self.strip.show()

    # --- początek wyświetlania: budowanie nowego obrazu --------------------------
    def _intro_fill(self, target: List[int]) -> None:
        """Klasyczne wypełnianie diody po diodzie od początku paska."""
        for i, color in enumerate(target):
            self._set(i, color)
            self.strip.show()
            time.sleep(config.PIXEL_DELAY_S)

    def _intro_drop(self, target: List[int], frame_delay: float = 0.012, spacing: int = 2) -> None:
        """Kolorowe krople spadają od końca każdej skali i układają się w słupek od jej początku."""
        segments = [(0, config.LED_COUNT_EXT), (config.LED_COUNT_EXT, config.LED_COUNT_INT)]
        queues = [[i for i in range(start, start + length) if target[i] != OFF] for start, length in segments]
        ends = [start + length - 1 for start, length in segments]
        settled = [OFF] * len(target)
        falling: List[List[int]] = []  # [aktualna pozycja, docelowa dioda]
        frame = 0
        while any(queues) or falling:
            if frame % spacing == 0:  # co `spacing` klatek startuje kolejna kropla w każdej skali
                for queue, end in zip(queues, ends):
                    if queue:
                        falling.append([end, queue.pop(0)])
            image = list(settled)
            still_falling = []
            for position, dest in falling:
                if position <= dest:
                    settled[dest] = image[dest] = target[dest]
                else:
                    image[position] = target[dest]
                    still_falling.append([position - 1, dest])
            falling = still_falling
            for i, color in enumerate(image):
                self._set(i, color)
            self.strip.show()
            time.sleep(frame_delay)
            frame += 1

    def _intro_twinkle(self, target: List[int], duration: float = 2.0, flash_len: int = 3) -> None:
        """Diody pojawiają się w losowej kolejności: najpierw białym błyskiem, potem we właściwym kolorze."""
        lit = [i for i, color in enumerate(target) if color != OFF]
        if not lit:
            return
        random.shuffle(lit)
        delay = duration / len(lit)
        flash = Color(255, 255, 255)
        recent: List[int] = []
        for i in lit:
            self._set(i, flash)
            recent.append(i)
            if len(recent) > flash_len:
                settled = recent.pop(0)
                self._set(settled, target[settled])
            self.strip.show()
            time.sleep(delay)
        for i in recent:
            self._set(i, target[i])
        self.strip.show()

    def _intro_rainbow(self, target: List[int], lead_frames: int = 30, fps: int = 50) -> None:
        """Najpierw tęcza płynie po całym pasku, potem od początku paska zamienia się w obraz docelowy."""
        n = self.strip.numPixels()
        for frame in range(lead_frames + n + 1):
            revealed = max(0, frame - lead_frames)
            for i in range(n):
                self._set(i, target[i] if i < revealed else wheel(i * 256 // n + frame * 8))
            self.strip.show()
            time.sleep(1 / fps)
