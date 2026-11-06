"""Odczyt temperatur: czujnik DS18B20 (dom) i czujnik Aqara przez Zigbee2MQTT (zewnątrz)."""

import logging
import os
import re
import subprocess
from typing import Optional

from w1thermsensor import W1ThermSensor

import config

log = logging.getLogger(__name__)

# Dopasowuje fragment payloadu MQTT w dzienniku, np.  "temperature":8.98
_TEMPERATURE_RE = re.compile(r'temperature\\?"\s*:\s*(-?\d+(?:\.\d+)?)')


def read_indoor() -> float:
    """Temperatura w domu z DS18B20. Przy awarii czujnika rzuca wyjątek."""
    return W1ThermSensor().get_temperature()


def parse_outdoor_temperature(log_text: str, device_id: Optional[str] = None) -> Optional[float]:
    """Zwraca OSTATNI odczyt temperatury z tekstu dziennika albo None, gdy go brak."""
    if device_id:
        log_text = "\n".join(line for line in log_text.splitlines() if device_id in line)
    matches = _TEMPERATURE_RE.findall(log_text)
    return float(matches[-1]) if matches else None


def read_outdoor() -> Optional[float]:
    """Temperatura zewnętrzna z dziennika Zigbee2MQTT albo None, gdy nie udało się jej odczytać."""
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

    return parse_outdoor_temperature(result.stdout, config.ZIGBEE_DEVICE_ID)
