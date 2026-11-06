"""Obsługa pasków LED: skale temperatury i proste animacje."""

import time

from rpi_ws281x import Adafruit_NeoPixel, Color

import config
from colors import COLORS_EXT, COLORS_INT

OFF = 0x000000


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def lit_count(temperature: int, min_temp: int, led_count: int) -> int:
    """Ile diod ma się zaświecić dla danej temperatury (0 ... led_count).

    Pierwsza dioda zapala się przy min_temp, każdy kolejny stopień dokłada jedną.
    Wartości spoza skali są obcinane, więc upał ani mróz nie psują programu.
    """
    return _clamp(temperature - min_temp + 1, 0, led_count)


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

    def clear(self) -> None:
        """Gasi wszystkie diody naraz."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, OFF)
        self.strip.show()

    def wipe(self, color: int, wait_s: float = 0.05) -> None:
        """Zapala (lub gasi, dla koloru 0) kolejne diody jedna po drugiej."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_s)

    def turn_off(self) -> None:
        self.wipe(Color(0, 0, 0), 0.01)

    def _draw_scale(self, palette, offset: int, lit: int) -> None:
        for i, color in enumerate(palette):
            self.strip.setPixelColor(offset + i, color if i < lit else OFF)
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
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(0.01)
        for i, color in enumerate(COLORS_INT):
            self.strip.setPixelColor(config.LED_COUNT_EXT + i, color)
            self.strip.show()
            time.sleep(0.03)
