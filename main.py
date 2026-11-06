"""Termometr LED: pokazuje temperaturę w domu i na zewnątrz na paskach LED
i wysyła pomiary do repozytorium GitHub.

Uruchomienie (wymaga roota ze względu na paski LED):  sudo python3 main.py
"""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Optional

import config
import sensors
from display import LedDisplay
from publisher import GithubPublisher

log = logging.getLogger("termometr")


class Thermometer:
    def __init__(self, publisher: Optional[GithubPublisher]) -> None:
        self.publisher = publisher
        self.display: Optional[LedDisplay] = None
        self.outdoor = 0.0  # ostatni znany odczyt zewnętrzny (0 do czasu pierwszego odczytu)
        self.loops = 0

    def cycle(self) -> None:
        """Jeden obieg: odczyt, rysowanie na LED, ewentualna wysyłka na GitHub."""
        indoor = sensors.read_indoor()
        new_outdoor = sensors.read_outdoor()
        if new_outdoor is not None:
            self.outdoor = new_outdoor

        self.display.clear()
        time.sleep(config.CLEAR_PAUSE_S)
        self.display.show_temps(round(self.outdoor), round(indoor))

        local_time = datetime.now().strftime("%H:%M:%S")
        log.info("%s | DS18B20 (dom): %s °C | Aqara (zewnątrz): %s °C", local_time, indoor, self.outdoor)

        self.loops += 1
        if self.loops >= config.PUBLISH_EVERY_N_LOOPS:
            self.loops = 0
            if self.publisher is not None:
                self.publisher.publish_readings(indoor, self.outdoor, local_time)

        time.sleep(config.LOOP_PAUSE_S)

    def shutdown(self) -> None:
        if self.display is not None:
            try:
                self.display.turn_off()
            except Exception as exc:
                log.warning("Nie udało się zgasić diod: %s", exc)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # systemd zatrzymuje usługę przez SIGTERM, więc też kończymy czysto (z zgaszeniem diod)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    publisher = None
    if config.GITHUB_TOKEN:
        publisher = GithubPublisher(config.GITHUB_TOKEN, config.GITHUB_REPO, config.GITHUB_BRANCH)
    else:
        log.warning("Brak GITHUB_TOKEN: wysyłka na GitHub jest wyłączona (LED działają normalnie)")

    thermometer = Thermometer(publisher)
    try:
        while True:
            try:
                if thermometer.display is None:
                    thermometer.display = LedDisplay()
                thermometer.cycle()
            except Exception:
                log.exception("Błąd w pętli głównej, ponowna próba za %s s", config.RESTART_DELAY_S)
                thermometer.display = None
                time.sleep(config.RESTART_DELAY_S)
    except (KeyboardInterrupt, SystemExit):
        log.info("Zatrzymywanie...")
    finally:
        thermometer.shutdown()


if __name__ == "__main__":
    main()
