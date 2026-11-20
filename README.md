# Termometr LED

Program na Raspberry Pi, który pokazuje na paskach LED temperaturę w salonie
(czujnik Aqara przez Zigbee2MQTT) i na zewnątrz (czujnik Tuya „sypialnia”, zamontowany
za oknem) oraz co kilka minut wysyła pomiary do repozytorium `velvethome.github.io`.
Czujniki Tuya (pralnia, sypialnia) są odczytywane przez chmurę Tuya.

## Struktura

| Plik | Co robi |
|---|---|
| `main.py` | pętla główna, obsługa błędów i zatrzymania |
| `config.py` | **wszystkie ustawienia** (piny, czasy, repozytorium, zakresy skal) |
| `sensors.py` | odczyt temperatury i wilgotności Aqara (salon) z dziennika Zigbee2MQTT |
| `display.py` | rysowanie skal temperatury i animacje na LED |
| `colors.py` | palety kolorów obu skal |
| `tuya_sensors.py` | odczyt czujników Tuya (pralnia, sypialnia) z chmury Tuya |
| `publisher.py` | wysyłka `temperatures.txt`, `monkey.txt` i `temperatures_<nazwa>.txt` na GitHub |
| `tools/led_test.py` | test sprzętu LED |

## Instalacja

```bash
pip3 install -r requirements.txt
cp .env.example .env      # i wpisz w nim nowy token GitHuba
cp /home/pi/Projekty/tinytuya.json .   # klucze projektu Tuya (plik jest w .gitignore)
```

Bez pliku `tinytuya.json` program działa, tylko bez czujników Tuya (ostrzeżenie w logu).

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

- `temperatures.txt`: jedna linia na pomiar, `<czas ISO Warszawa>,<salon>,<zewnątrz>`, maksymalnie ok. 800 linii
- `monkey.txt`: trzy linie, `<salon>`, `<zewnątrz>`, `<HH:MM:SS>`
- `temperatures_salon.txt` (Aqara, co ok. 2 min), `temperatures_pralnia.txt` i `temperatures_sypialnia.txt`
  (Tuya, co 5 min; sypialnia to czujnik za oknem, na stronie i w aplikacji „Na zewnątrz”):
  jedna linia na pomiar, `<czas ISO Warszawa>,<temperatura>,<wilgotność>`, tylko ostatnie 24 h
  (czytają je strona licznika gazu i aplikacja)

## Efekty przy odświeżaniu

Każde odświeżenie ma dwa etapy i na każdym działa osobny efekt (domyślnie losowy,
nigdy ten sam dwa razy z rzędu):

- **Koniec wyświetlania** (gaszenie starego obrazu): `fade`, `dissolve`, `comet`, `rainbow`, `curtain`, `clear`
- **Początek wyświetlania** (pojawianie się nowych temperatur): `fill`, `drop`, `twinkle`, `comet`, `rainbow`, `curtain`

W `config.py` ustaw `TRANSITION` i `INTRO` na `"random"` (losowanie z list `TRANSITIONS_ENABLED`
i `INTROS_ENABLED`) albo na nazwę jednego efektu. Nowy efekt dodasz jako metodę w `display.py`
i wpisem w słowniku `_transitions` lub `_intros`.

## Najczęstsze zmiany

- Inna jasność lub piny LED: `config.py`, sekcja *Paski LED*
- Inny zakres skali (np. skala domowa od 15 °C): `EXT_MIN_TEMP` / `INT_MIN_TEMP` w `config.py` oraz paleta w `colors.py`
- Częstsza wysyłka na GitHub: `PUBLISH_EVERY_N_LOOPS`
- Kilka czujników Zigbee: ustaw `ZIGBEE_DEVICE_ID` na identyfikator czujnika w salonie
- Nowy czujnik Tuya: dopisz go do `TUYA_DEVICES` w `config.py` (plik `temperatures_<nazwa>.txt` utworzy się sam)
- Częstość odczytu Tuya: `TUYA_INTERVAL_S` (uwaga na limit zapytań projektu w chmurze Tuya)
- Odczyty Tuya z wilgotnością spoza zakresu (0, 100] % (np. same zera z chmury) są pomijane;
  w logu pojawia się wtedy ostrzeżenie z pełnym statusem czujnika
- Źródło temperatury zewnętrznej: `OUTDOOR_TUYA_SENSOR` (nazwa czujnika z `TUYA_DEVICES`).
  Gdy jego odczyt jest starszy niż `OUTDOOR_MAX_AGE_S`, w logu pojawia się ostrzeżenie,
  a na diodach zostaje ostatnia znana wartość
