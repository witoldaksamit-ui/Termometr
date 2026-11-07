"""Test sprzętu LED (zastępuje dawny LED_test.py).

Uruchom z katalogu projektu:
    sudo python3 tools/led_test.py            # animacja wypełniania kolorem (Ctrl+C kończy)
    sudo python3 tools/led_test.py --palette  # pełne palety obu skal
    sudo python3 tools/led_test.py --transitions  # podgląd efektów gaszenia (koniec wyświetlania)
    sudo python3 tools/led_test.py --intros       # podgląd efektów rysowania (początek wyświetlania)
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rpi_ws281x import Color  # noqa: E402

from display import LedDisplay  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Test pasków LED termometru")
    parser.add_argument("--palette", action="store_true", help="pokaż pełne palety skal")
    parser.add_argument("--transitions", action="store_true", help="pokaż po kolei efekty gaszenia")
    parser.add_argument("--intros", action="store_true", help="pokaż po kolei efekty rysowania temperatur")
    args = parser.parse_args()

    display = LedDisplay()
    try:
        if args.palette:
            display.show_palette()
            time.sleep(10)
        elif args.transitions:
            for name in ("fade", "dissolve", "comet", "rainbow", "curtain", "clear"):
                print(f"Przejście: {name}")
                display.show_temps(outdoor=8, indoor=21)
                time.sleep(1)
                display.transition(name)
        elif args.intros:
            for name in ("fill", "fade", "twinkle", "comet", "rainbow", "curtain"):
                print(f"Początek: {name}")
                display.show_temps(outdoor=8, indoor=21, intro=name)
                time.sleep(2)
                display.transition("clear")
        else:
            while True:
                print("Color wipe...")
                display.wipe(Color(137, 83, 237))
                time.sleep(5)
                display.clear()
    except KeyboardInterrupt:
        pass
    finally:
        display.turn_off()


if __name__ == "__main__":
    main()
