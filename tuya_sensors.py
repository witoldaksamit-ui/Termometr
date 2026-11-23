"""Odczyt czujników temperatury i wilgotności Tuya (pralnia, sypialnia, dwór) osuszacza i sterownika pieca przez chmurę Tuya.

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


class Dehumidifier(NamedTuple):
    """Stan osuszacza Warmtec ODT-12N Wi-Fi (surowe dane DP z chmury Tuya)."""
    on: bool        # switch_on
    mode: int       # set_mode: 0 = wilgotność docelowa (DRY, COMFORT = cel 60 %), 1 = ciągłe (CONT albo TURBO)
    target: int     # set_temper: wilgotność docelowa w %
    fan: int        # wind_speed: 0 = niski, 2 = wysoki (1 = średni osuszacz ignoruje)
    humidity: int   # f_temper: wilgotność zmierzona przez osuszacz w %
    fault: int      # fault: bitmapa, bity 0-5 = P1, E3, E5, EH, E1, E2; bit 6 (64) = pełny zbiornik


def dehumidifier_from_properties(properties: list) -> Optional[Dehumidifier]:
    """Stan osuszacza z listy właściwości (shadow properties); None, gdy brakuje danych."""
    v = {p.get("code"): p.get("value") for p in properties}
    try:
        return Dehumidifier(
            on=bool(v["switch_on"]),
            mode=int(v["set_mode"]),
            target=int(v["set_temper"]),
            fan=int(v["wind_speed"]),
            humidity=int(v["f_temper"]),
            fault=int(v.get("fault") or 0),
        )
    except (KeyError, TypeError, ValueError):
        return None


class Thermostat(NamedTuple):
    """Stan sterownika pieca ENGO E901 Wi-Fi (surowe dane DP z chmury Tuya)."""
    temperature: float   # temp_current, °C (w chmurze w dziesiątych częściach stopnia)
    target: float        # temp_set, °C
    heating: bool        # concise_work_state == heating_on: piec grzeje
    mode: str            # run_mode: program / manual / holiday / temporary / boost / frost
    battery: Optional[int]  # battery_percentage termostatu
    online: bool         # tx_online_flag: termostat połączony z odbiornikiem przy piecu
    fault: int           # fault: bit 0 = błąd czujnika temperatury (ErrorNTC)
    on: bool             # switch2


def thermostat_from_properties(properties: list) -> Optional[Thermostat]:
    """Stan sterownika pieca z listy właściwości (shadow properties); None, gdy brakuje danych."""
    v = {p.get("code"): p.get("value") for p in properties}
    try:
        state = v.get("concise_work_state") or v.get("work_state") or ""
        battery = v.get("battery_percentage")
        return Thermostat(
            temperature=int(v["temp_current"]) / 10,
            target=int(v["temp_set"]) / 10,
            heating=str(state) in ("heating_on", "heating", "heating_low_temp", "manual_on", "tx_lost_heating"),
            mode=str(v.get("run_mode") or ""),
            battery=int(battery) if battery is not None else None,
            online=bool(v.get("tx_online_flag", True)),
            fault=int(v.get("fault") or 0),
            on=bool(v.get("switch2", True)),
        )
    except (KeyError, TypeError, ValueError):
        return None


def is_valid(temperature: float, humidity: float) -> bool:
    """Odczyt jest wiarygodny, gdy wilgotność mieści się w (0, 100] %.
    Temperatura 0 °C jest prawidłowa (zima), dlatego o odrzuceniu decyduje tylko wilgotność."""
    return 0 < humidity <= 100


class TuyaReader:
    def __init__(self, config_file, devices: Dict[str, str], interval_s: float,
                 dehumidifier_id: Optional[str] = None, thermostat_id: Optional[str] = None) -> None:
        self._config_file = config_file
        self._devices = devices
        self._dehumidifier_id = dehumidifier_id
        self._new_dehumidifier: Optional[Dehumidifier] = None  # nowy odczyt osuszacza, do odebrania
        self._thermostat_id = thermostat_id
        self._new_thermostat: Optional[Thermostat] = None      # nowy odczyt sterownika pieca, do odebrania
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
        if self._dehumidifier_id:
            self._new_dehumidifier = self._read_shadow(cloud, "osuszacz", self._dehumidifier_id,
                                                       dehumidifier_from_properties)
        if self._thermostat_id:
            self._new_thermostat = self._read_shadow(cloud, "sterownik pieca", self._thermostat_id,
                                                     thermostat_from_properties)
        return readings

    def _read_shadow(self, cloud, label: str, device_id: str, parse):
        """Surowe dane urządzenia (DP): standardowy zestaw w chmurze bywa okrojony (osuszacz)
        albo nie zawiera np. stanu grzania (sterownik pieca)."""
        try:
            res = cloud.cloudrequest(f"/v2.0/cloud/thing/{device_id}/shadow/properties")
            if not res.get("success"):
                log.warning("Tuya %s: błąd odpowiedzi: %s", label, res)
                return None
            state = parse(res["result"]["properties"])
        except Exception as exc:
            log.warning("Tuya %s: nie udało się odczytać: %s", label, exc)
            return None
        if state is None:
            log.warning("Tuya %s: niepełne dane: %s", label, res)
        else:
            log.info("Tuya %s: %s", label, state)
        return state

    def take_thermostat(self) -> Optional[Thermostat]:
        """Zwraca nowy odczyt sterownika pieca (raz) albo None, gdy od ostatniego wywołania go nie było."""
        state, self._new_thermostat = self._new_thermostat, None
        return state

    def take_dehumidifier(self) -> Optional[Dehumidifier]:
        """Zwraca nowy odczyt osuszacza (raz) albo None, gdy od ostatniego wywołania go nie było."""
        state, self._new_dehumidifier = self._new_dehumidifier, None
        return state

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
    return TuyaReader(config.TUYA_CONFIG_FILE, config.TUYA_DEVICES, config.TUYA_INTERVAL_S,
                      config.DEHUMIDIFIER_ID, config.THERMOSTAT_ID)
