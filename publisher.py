"""Wysyłanie odczytów do repozytorium GitHub (commit z nową zawartością pliku).

Format plików jest "kontraktem" z innymi programami (aplikacja z temperaturą,
zegarek Garmin), więc nie zmieniaj go bez sprawdzenia, kto je czyta:

  temperatures.txt  - jedna linia na pomiar:  <czas ISO, Warszawa>,<dom>,<zewnątrz>
  monkey.txt        - trzy linie:             <dom> / <zewnątrz> / <HH:MM:SS>
"""

import logging
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from github import Auth, Github

import config

log = logging.getLogger(__name__)

COMMIT_MESSAGE = "Automated update from Python script"


class GithubPublisher:
    def __init__(self, token: str, repo_name: str, branch: str = "main") -> None:
        self._token = token
        self._repo_name = repo_name
        self._branch = branch
        self._repo = None  # tworzone przy pierwszym użyciu, żeby brak sieci nie wywalał startu

    def _get_repo(self):
        if self._repo is None:
            self._repo = Github(auth=Auth.Token(self._token)).get_repo(self._repo_name)
        return self._repo

    def _update_file(self, path: str, transform: Callable[[str], str]) -> None:
        """Pobiera plik, zamienia jego treść funkcją transform i zapisuje commit."""
        repo = self._get_repo()
        contents = repo.get_contents(path, ref=self._branch)
        old_text = contents.decoded_content.decode("utf-8")
        repo.update_file(
            path=contents.path,
            message=COMMIT_MESSAGE,
            content=transform(old_text),
            sha=contents.sha,
            branch=self._branch,
        )

    def publish_readings(self, indoor: float, outdoor: float, local_time: str) -> bool:
        """Dopisuje pomiar do historii i odświeża plik dla zegarka.

        Każdy plik jest aktualizowany osobno, więc błąd jednego nie blokuje drugiego.
        Zwraca True, jeśli oba zapisy się udały.
        """
        timestamp = datetime.now(ZoneInfo(config.TIMEZONE)).replace(microsecond=0).isoformat()
        entry = f"{timestamp},{indoor},{outdoor}"

        def add_entry(old_text: str) -> str:
            lines = old_text.splitlines()
            while len(lines) > config.TEMPERATURES_MAX_LINES:
                lines.pop(0)
            lines.append(entry)
            return "\n".join(lines)

        def latest_reading(_old_text: str) -> str:
            return f"{indoor}\n{outdoor}\n{local_time}"

        ok = True
        for path, transform in (
            (config.TEMPERATURES_FILE, add_entry),
            (config.GARMIN_FILE, latest_reading),
        ):
            try:
                self._update_file(path, transform)
                log.info("Zapisano %s na GitHubie", path)
            except Exception as exc:
                ok = False
                log.error("Nie udało się zapisać %s: %s", path, exc)
        return ok
