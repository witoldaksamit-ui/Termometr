"""Termometr LED: pokazuje temperaturę w domu i na zewnątrz na paskach LED
i wysyła pomiary do repozytorium GitHub.

Uruchomienie (wymaga roota ze względu na paski LED):  sudo python3 main.py
"""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import config
import sensors
import tuya_sensors
from display import LedDisplay
from publisher import GithubPublisher
from tuya_sensors import TuyaReader

log = logging.getLogger("termometr")


class Thermometer:
    def __init__(self, publisher: Optional[GithubPublisher], tuya: Optional[TuyaReader] = None) -> None:
        self.publisher = publisher
        self.tuya = tuya
        self.display: Optional[LedDisplay] = None
        self.outdoor = 0.0  # ostatni znany odczyt zewnętrzny (0 do czasu pierwszego odczytu)
        self.outdoor_source = "brak"
        # nazwa czujnika Tuya -> (temperatura, wilgotność, time.monotonic() odczytu)
        self.tuya_latest: Dict[str, Tuple[float, int, float]] = {}
        self.loops = 0

    def cycle(self) -> None:
        """Jeden obieg: odczyt, rysowanie na LED, ewentualna wysyłka na GitHub."""
        indoor = sensors.read_indoor()
        new_tuya = self.poll_tuya()
        self.update_outdoor()

        self.display.transition()
        self.display.show_temps(round(self.outdoor), round(indoor))

        local_time = datetime.now().strftime("%H:%M:%S")
        log.info("%s | DS18B20 (dom): %s °C | %s (zewnątrz): %s °C",
                 local_time, indoor, self.outdoor_source, self.outdoor)

        if self.publisher is not None:
            for name, (temp, hum) in new_tuya.items():
                self.publisher.publish_room(name, temp, hum)

        self.loops += 1
        if self.loops >= config.PUBLISH_EVERY_N_LOOPS:
            self.loops = 0
            if self.publisher is not None:
                self.publisher.publish_readings(indoor, self.outdoor, local_time)

        time.sleep(config.LOOP_PAUSE_S)

    def poll_tuya(self) -> Dict[str, Tuple[float, int]]:
        """Odczyt czujników Tuya (najczęściej co TUYA_INTERVAL_S). Zwraca tylko NOWE odczyty.
        Żaden błąd Tuya nie może przerwać pętli ani zgasić diod."""
        if self.tuya is None:
            return {}
        try:
            readings = self.tuya.read_if_due()
        except Exception:
            log.exception("Nieoczekiwany błąd odczytu czujników Tuya")
            return {}
        now = time.monotonic()
        for name, (temp, hum) in readings.items():
            self.tuya_latest[name] = (temp, hum, now)
        return readings

    def tuya_outdoor(self) -> Optional[float]:
        """Temperatura z czujnika Tuya wskazanego w OUTDOOR_TUYA_SENSOR, jeśli jest świeża."""
        name = config.OUTDOOR_TUYA_SENSOR
        if not name:
            return None
        reading = self.tuya_latest.get(name)
        if reading is None or time.monotonic() - reading[2] > config.OUTDOOR_MAX_AGE_S:
            return None
        return reading[0]

    def update_outdoor(self) -> None:
        """Temperatura zewnętrzna: najpierw czujnik Tuya, a gdy jego odczyt jest za stary
        lub go brak, czujnik Aqara (jeśli OUTDOOR_FALLBACK_AQARA). Bez nowego odczytu
        zostaje ostatnia znana wartość."""
        value = self.tuya_outdoor()
        if value is not None:
            self.outdoor, self.outdoor_source = value, f"Tuya {config.OUTDOOR_TUYA_SENSOR}"
            return
        if config.OUTDOOR_FALLBACK_AQARA or not config.OUTDOOR_TUYA_SENSOR:
            value = sensors.read_outdoor()
            if value is not None:
                self.outdoor, self.outdoor_source = value, "Aqara"

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

    tuya = tuya_sensors.create_reader()
    thermometer = Thermometer(publisher, tuya)
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
