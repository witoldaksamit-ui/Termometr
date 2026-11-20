"""Odczyt czujników temperatury i wilgotności Tuya (pralnia, sypialnia) przez chmurę Tuya.

Zastępuje osobny skrypt odczyt.py. Błędy chmury (brak sieci, limit zapytań, zły klucz)
nigdy nie przerywają pętli głównej: odczyt danego czujnika jest wtedy po prostu pomijany.
"""

import json
import logging
import time
from typing import Dict, NamedTuple, Optional, Union

import config

log = logging.getLogger(__name__)

class Reading(NamedTuple):
    temperature: float                  # °C
    humidity: int                       # %
    battery: Optional[Union[int, str]]  # procent (np. 85) albo stan ("low" / "middle" / "high"); None, gdy brak


# Kody Tuya, pod którymi czujniki podają stan baterii (zależnie od modelu)
_BATTERY_CODES = ("battery_percentage", "va_battery", "battery_value", "battery_state", "battery")


def battery_from_status(status: dict) -> Optional[Union[int, str]]:
    """Stan baterii ze statusu Tuya: procent (int) albo stan tekstowy; None, gdy czujnik go nie podaje."""
    for code in _BATTERY_CODES:
        if code in status and status[code] is not None:
            value = status[code]
            return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
    return None


def is_valid(temperature: float, humidity: float) -> bool:
    """Odczyt jest wiarygodny, gdy wilgotność mieści się w (0, 100] %.
    Temperatura 0 °C jest prawidłowa (zima), dlatego o odrzuceniu decyduje tylko wilgotność."""
    return 0 < humidity <= 100


class TuyaReader:
    def __init__(self, config_file, devices: Dict[str, str], interval_s: float) -> None:
        self._config_file = config_file
        self._devices = devices
        self._interval_s = interval_s
        self._cloud = None
        self._last_read = 0.0  # time.monotonic() ostatniej próby odczytu

    def _get_cloud(self):
        if self._cloud is None:
            import tinytuya  # import tutaj, żeby brak biblioteki nie blokował startu termometru

            with open(self._config_file, encoding="utf-8") as f:
                cfg = json.load(f)
            self._cloud = tinytuya.Cloud(
                apiRegion=cfg["apiRegion"],
                apiKey=cfg["apiKey"],
                apiSecret=cfg["apiSecret"],
                apiDeviceID=next(iter(self._devices.values())),
            )
        return self._cloud

    def read_all(self) -> Dict[str, Reading]:
        """Odczytuje wszystkie czujniki. Zwraca tylko te, które udało się odczytać."""
        self._last_read = time.monotonic()
        try:
            cloud = self._get_cloud()
        except Exception as exc:
            log.warning("Tuya: nie można połączyć się z chmurą: %s", exc)
            self._cloud = None
            return {}

        readings: Dict[str, Reading] = {}
        for name, device_id in self._devices.items():
            try:
                res = cloud.getstatus(device_id)
                if not res.get("success"):
                    log.warning("Tuya %s: błąd odpowiedzi: %s", name, res)
                    continue
                status = {item["code"]: item["value"] for item in res["result"]}
                temp = status["va_temperature"] / 10
                hum = status["va_humidity"]
            except Exception as exc:
                log.warning("Tuya %s: nie udało się odczytać: %s", name, exc)
                continue
            if not is_valid(temp, hum):
                # Wilgotność 0 % nie występuje w rzeczywistości: to pusty status z chmury
                # (np. czujnik po restarcie jeszcze nie zmierzył). Pełny status pomaga ustalić przyczynę.
                log.warning("Tuya %s: odrzucony odczyt %s °C, %s %% (pełny status: %s)", name, temp, hum, status)
                continue
            battery = battery_from_status(status)
            readings[name] = Reading(temp, hum, battery)
            log.info("Tuya %s: %s °C, %s %%, bateria: %s", name, temp, hum, battery)
        return readings

    def read_if_due(self) -> Dict[str, Reading]:
        """Odczytuje czujniki, jeśli od ostatniej próby minęło co najmniej interval_s.
        W przeciwnym razie zwraca pusty słownik (bez zapytań do chmury)."""
        if self._last_read and time.monotonic() - self._last_read < self._interval_s:
            return {}
        return self.read_all()


def create_reader() -> Optional[TuyaReader]:
    """Tworzy czytnik Tuya albo zwraca None, gdy czujniki są wyłączone lub brakuje konfiguracji."""
    if not config.TUYA_DEVICES:
        return None
    if not config.TUYA_CONFIG_FILE.is_file():
        log.warning("Brak pliku %s: odczyt czujników Tuya jest wyłączony", config.TUYA_CONFIG_FILE)
        return None
    return TuyaReader(config.TUYA_CONFIG_FILE, config.TUYA_DEVICES, config.TUYA_INTERVAL_S)
