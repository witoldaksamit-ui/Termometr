"""Obsługa pasków LED: skale temperatury, animacje i przejścia między odświeżeniami."""

import logging
import random
import time
from typing import Optional

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
        self._frame = [OFF] * config.LED_COUNT  # to, co aktualnie świeci
        self._last_transition: Optional[str] = None
        self._transitions = {
            "clear": self.clear,
            "fade": self._fade_out,
            "dissolve": self._dissolve,
            "comet": self._comet,
            "rainbow": self._rainbow,
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

    # --- skale temperatury -----------------------------------------------------
    def _draw_scale(self, palette, offset: int, lit: int) -> None:
        for i, color in enumerate(palette):
            self._set(offset + i, color if i < lit else OFF)
            self.strip.show()
            time.sleep(config.PIXEL_DELAY_S)

    def show_temps(self, outdoor: int, indoor: int) -> None:
        """Rysuje obie skale: zewnętrzną (diody od 0) i domową (zaraz po niej)."""
        lit_ext = lit_count(outdoor, config.EXT_MIN_TEMP, config.LED_COUNT_EXT)
        lit_int = lit_count(indoor, config.INT_MIN_TEMP, config.LED_COUNT_INT)
        self._draw_scale(COLORS_EXT, 0, lit_ext)
        self._draw_scale(COLORS_INT, config.LED_COUNT_EXT, lit_int)

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

    # --- przejścia (kończą się zawsze na zgaszonym pasku) ----------------------
    def transition(self, name: Optional[str] = None) -> None:
        """Gasi aktualny obraz wybranym efektem, a potem robi krótką przerwę w ciemności."""
        name = name or config.TRANSITION
        if name == "random":
            choices = [n for n in config.TRANSITIONS_ENABLED if n in self._transitions]
            if len(choices) > 1 and self._last_transition in choices:
                choices.remove(self._last_transition)  # nie powtarzaj tego samego dwa razy z rzędu
            name = random.choice(choices) if choices else "clear"
        if name not in self._transitions:
            log.warning("Nieznane przejście '%s', używam 'clear'", name)
            name = "clear"

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

    def _comet(self, tail: int = 8, delay: float = 0.015) -> None:
        """Kolorowa kometa z ogonem przebiega przez pasek i zmiata stary obraz."""
        n = self.strip.numPixels()
        hue = random.randrange(256)
        for pos in range(n + tail):
            for k in range(tail):
                index = pos - k
                if 0 <= index < n:
                    factor = 1.0 if k == 0 else (1 - k / tail) ** 2
                    self._set(index, scale_color(wheel(hue + k * 6), factor))
            behind = pos - tail
            if 0 <= behind < n:
                self._set(behind, OFF)
            self.strip.show()
            time.sleep(delay)

    def _rainbow(self, duration: float = 1.5, fps: int = 50) -> None:
        """Tęcza przesuwa się po całym pasku, a potem płynnie gaśnie."""
        n = self.strip.numPixels()
        for frame in range(int(duration * fps)):
            for i in range(n):
                self._set(i, wheel(i * 256 // n + frame * 8))
            self.strip.show()
            time.sleep(1 / fps)
        self._fade_out()

    def _curtain(self, delay: float = 0.03) -> None:
        """Dwa kolorowe światełka ruszają od końców paska i zamykają go jak kurtynę."""
        n = self.strip.numPixels()
        for k in range((n + 1) // 2):
            left, right = k, n - 1 - k
            color = wheel(k * 6)
            self._set(left, color)
            self._set(right, color)
            if k > 0:
                self._set(left - 1, OFF)
                self._set(right + 1, OFF)
            self.strip.show()
            time.sleep(delay)
