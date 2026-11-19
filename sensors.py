"""Odczyt czujnika Aqara (salon) przez Zigbee2MQTT: temperatura i wilgotność z dziennika usługi."""

import logging
import os
import re
import subprocess
from typing import NamedTuple, Optional

import config

log = logging.getLogger(__name__)

# Dopasowują fragment payloadu MQTT w dzienniku, np.  "temperature":21.98  /  "humidity":45.2
# (cudzysłów bywa poprzedzony ukośnikiem, gdy payload jest zapisany jako tekst w logu)
_TEMPERATURE_RE = re.compile(r'temperature\\?"\s*:\s*(-?\d+(?:\.\d+)?)')
_HUMIDITY_RE = re.compile(r'humidity\\?"\s*:\s*(-?\d+(?:\.\d+)?)')


class AqaraReading(NamedTuple):
    temperature: float
    humidity: Optional[float]  # None, gdy w dzienniku nie ma wilgotności


def parse_aqara(log_text: str, device_id: Optional[str] = None) -> Optional[AqaraReading]:
    """Zwraca OSTATNI odczyt z tekstu dziennika albo None, gdy brak temperatury.
    Temperaturę i wilgotność bierze z tej samej (ostatniej) linii z temperaturą."""
    lines = log_text.splitlines()
    if device_id:
        lines = [line for line in lines if device_id in line]
    for line in reversed(lines):
        temps = _TEMPERATURE_RE.findall(line)
        if not temps:
            continue
        hums = _HUMIDITY_RE.findall(line)
        return AqaraReading(float(temps[-1]), float(hums[-1]) if hums else None)
    return None


def read_aqara() -> Optional[AqaraReading]:
    """Odczyt Aqara z dziennika Zigbee2MQTT albo None, gdy nie udało się go odczytać."""
    cmd = [
        "journalctl",
        "-u", config.ZIGBEE_SERVICE,
        "-n", str(config.ZIGBEE_JOURNAL_LINES),
        "--no-pager",
    ]
    if os.geteuid() != 0:
        cmd.insert(0, "sudo")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError) as exc:
        log.warning("Nie udało się odczytać dziennika Zigbee2MQTT: %s", exc)
        return None

    if result.returncode != 0:
        log.warning("journalctl zakończył się kodem %s: %s", result.returncode, result.stderr.strip())
        return None

    return parse_aqara(result.stdout, config.ZIGBEE_DEVICE_ID)
