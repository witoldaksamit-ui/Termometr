"""Termometr LED: pokazuje temperaturę w salonie (Aqara przez Zigbee2MQTT) i na zewnątrz
(czujnik Tuya) na paskach LED i wysyła pomiary do repozytorium GitHub.

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
        # ostatnie znane odczyty (None do czasu pierwszego odczytu)
        self.indoor: Optional[float] = None
        self.indoor_humidity: Optional[float] = None
        self.outdoor: Optional[float] = None
        # nazwa czujnika Tuya -> (temperatura, wilgotność, time.monotonic() odczytu)
        self.tuya_latest: Dict[str, Tuple[float, int, float]] = {}
        self.loops = 0

    def cycle(self) -> None:
        """Jeden obieg: odczyt, rysowanie na LED, ewentualna wysyłka na GitHub."""
        self.update_indoor()
        new_tuya = self.poll_tuya()
        self.update_outdoor()

        self.display.transition()
        self.display.show_temps(self.led_value(self.outdoor, config.EXT_MIN_TEMP),
                                self.led_value(self.indoor, config.INT_MIN_TEMP))

        local_time = datetime.now().strftime("%H:%M:%S")
        log.info("%s | Aqara (salon): %s °C, %s %% | Tuya %s (zewnątrz): %s °C",
                 local_time, self.indoor, self.indoor_humidity, config.OUTDOOR_TUYA_SENSOR, self.outdoor)

        if self.publisher is not None:
            for name, (temp, hum) in new_tuya.items():
                self.publisher.publish_room(name, temp, hum)

        self.loops += 1
        if self.loops >= config.PUBLISH_EVERY_N_LOOPS:
            self.loops = 0
            if self.publisher is not None:
                if self.indoor is None or self.outdoor is None:
                    log.warning("Brak odczytu salonu lub zewnętrznego: pomijam zapis temperatures.txt")
                else:
                    self.publisher.publish_readings(self.indoor, self.outdoor, local_time)

        time.sleep(config.LOOP_PAUSE_S)

    @staticmethod
    def led_value(temp: Optional[float], scale_min: int) -> int:
        """Wartość do narysowania na diodach. Bez odczytu skala zostaje zgaszona."""
        return round(temp) if temp is not None else scale_min - 1

    def update_indoor(self) -> None:
        """Temperatura i wilgotność w salonie z Aqara. Bez nowego odczytu zostaje ostatnia wartość."""
        reading = sensors.read_aqara()
        if reading is not None:
            self.indoor = reading.temperature
            if reading.humidity is not None:
                self.indoor_humidity = reading.humidity

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

    def update_outdoor(self) -> None:
        """Temperatura zewnętrzna z czujnika Tuya OUTDOOR_TUYA_SENSOR. Gdy odczyt jest starszy
        niż OUTDOOR_MAX_AGE_S, zostaje ostatnia znana wartość (z ostrzeżeniem w logu)."""
        reading = self.tuya_latest.get(config.OUTDOOR_TUYA_SENSOR)
        if reading is None:
            return
        age = time.monotonic() - reading[2]
        if age > config.OUTDOOR_MAX_AGE_S:
            log.warning("Odczyt Tuya %s ma %d min, pokazuję ostatnią znaną temperaturę zewnętrzną",
                        config.OUTDOOR_TUYA_SENSOR, age // 60)
        self.outdoor = reading[0]

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
