# Termometr LED

Program na Raspberry Pi, który pokazuje na paskach LED temperaturę w domu
(czujnik DS18B20) i na zewnątrz (czujnik Aqara przez Zigbee2MQTT) oraz co kilka
minut wysyła pomiary do repozytorium `velvethome.github.io`.

## Struktura

| Plik | Co robi |
|---|---|
| `main.py` | pętla główna, obsługa błędów i zatrzymania |
| `config.py` | **wszystkie ustawienia** (piny, czasy, repozytorium, zakresy skal) |
| `sensors.py` | odczyt DS18B20 i temperatury zewnętrznej z dziennika Zigbee2MQTT |
| `display.py` | rysowanie skal temperatury i animacje na LED |
| `colors.py` | palety kolorów obu skal |
| `publisher.py` | wysyłka `temperatures.txt` i `monkey.txt` na GitHub |
| `tools/led_test.py` | test sprzętu LED |

## Instalacja

```bash
pip3 install -r requirements.txt
cp .env.example .env      # i wpisz w nim nowy token GitHuba
```

Token: GitHub → Settings → Developer settings → Fine-grained tokens, dostęp tylko
do `velvethome.github.io`, uprawnienie *Contents: Read and write*.
Plik `.env` jest w `.gitignore`. Nigdy nie wpisuj tokena do kodu.

## Uruchomienie

```bash
sudo python3 main.py
```

Bez `GITHUB_TOKEN` program działa, tylko bez wysyłki na GitHub (zobaczysz ostrzeżenie w logu).

### Jako usługa systemd

`/etc/systemd/system/termometr.service` (dostosuj ścieżki i nazwę użytkownika):

```ini
[Unit]
Description=Termometr LED
After=network-online.target zigbee2mqtt.service
Wants=network-online.target

[Service]
User=root
WorkingDirectory=/home/pi/Termometr
EnvironmentFile=/home/pi/Termometr/.env
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now termometr
journalctl -u termometr -f      # podgląd logów
```

## Test diod

```bash
sudo python3 tools/led_test.py             # animacja koloru
sudo python3 tools/led_test.py --palette   # pełne palety skal
sudo python3 tools/led_test.py --transitions   # podgląd efektów gaszenia
sudo python3 tools/led_test.py --intros        # podgląd efektów rysowania temperatur
```

Przed testem zatrzymaj główny program (`sudo pkill -f main.py`), bo dwa programy nie mogą naraz sterować paskiem.

## Formaty plików wysyłanych na GitHub

Czytają je inne programy (aplikacja z temperaturą, zegarek Garmin), więc nie zmieniaj formatu bez sprawdzenia:

- `temperatures.txt`: jedna linia na pomiar, `<czas ISO Warszawa>,<dom>,<zewnątrz>`, maksymalnie ok. 800 linii
- `monkey.txt`: trzy linie, `<dom>`, `<zewnątrz>`, `<HH:MM:SS>`

## Efekty przy odświeżaniu

Każde odświeżenie ma dwa etapy i na każdym działa osobny efekt (domyślnie losowy,
nigdy ten sam dwa razy z rzędu):

- **Koniec wyświetlania** (gaszenie starego obrazu): `fade`, `dissolve`, `comet`, `rainbow`, `curtain`, `clear`
- **Początek wyświetlania** (pojawianie się nowych temperatur): `fill`, `fade`, `twinkle`, `comet`, `rainbow`, `curtain`

W `config.py` ustaw `TRANSITION` i `INTRO` na `"random"` (losowanie z list `TRANSITIONS_ENABLED`
i `INTROS_ENABLED`) albo na nazwę jednego efektu. Nowy efekt dodasz jako metodę w `display.py`
i wpisem w słowniku `_transitions` lub `_intros`.

## Najczęstsze zmiany

- Inna jasność lub piny LED: `config.py`, sekcja *Paski LED*
- Inny zakres skali (np. skala domowa od 15 °C): `EXT_MIN_TEMP` / `INT_MIN_TEMP` w `config.py` oraz paleta w `colors.py`
- Częstsza wysyłka na GitHub: `PUBLISH_EVERY_N_LOOPS`
- Kilka czujników Zigbee: ustaw `ZIGBEE_DEVICE_ID` na identyfikator czujnika zewnętrznego
