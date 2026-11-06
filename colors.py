"""Palety kolorów dla pasków LED.

Każda lista ma jeden kolor na jedną diodę. Dioda o indeksie i zapala się,
gdy temperatura jest równa lub wyższa niż temperatura podana w komentarzu.
Zakresy skal ustawia config.py (EXT_MIN_TEMP, INT_MIN_TEMP), a długości list
muszą się zgadzać z LED_COUNT_EXT i LED_COUNT_INT.
"""

COLORS_EXT = [  # temperatura zewnętrzna, od -20 °C (61 diod)
    0x00FFFF,  # -20 °C
    0x0FFFFF,  # -19 °C
    0x1FFFFF,  # -18 °C
    0x2EFFFF,  # -17 °C
    0x3DFFFF,  # -16 °C
    0x54FFFF,  # -15 °C
    0x6BFFFF,  # -14 °C
    0x82FFFF,  # -13 °C
    0x99FFFF,  # -12 °C
    0xCCFFFF,  # -11 °C
    0xFFFFFF,  # -10 °C
    0xE6B2FF,  # -9 °C
    0xCC66FF,  # -8 °C
    0xAD57FF,  # -7 °C
    0x8F47FF,  # -6 °C
    0x7038FF,  # -5 °C
    0x5229FF,  # -4 °C
    0x3D1FFF,  # -3 °C
    0x2914FF,  # -2 °C
    0x140AFF,  # -1 °C
    0x0000FF,  # +0 °C
    0xFF0000,  # +1 °C
    0xFF140A,  # +2 °C
    0xFF331A,  # +3 °C
    0xFF5C2E,  # +4 °C
    0xFF8542,  # +5 °C
    0xFFAD57,  # +6 °C
    0xFFCC66,  # +7 °C
    0xFFD652,  # +8 °C
    0xFFE03D,  # +9 °C
    0xFFE82E,  # +10 °C
    0xFFF01F,  # +11 °C
    0xFFF70F,  # +12 °C
    0xFFFF00,  # +13 °C
    0xFAFF00,  # +14 °C
    0xF2FF00,  # +15 °C
    0xEBFF00,  # +16 °C
    0xE0FF00,  # +17 °C
    0xD6FF00,  # +18 °C
    0xCCFF00,  # +19 °C
    0xC2FF00,  # +20 °C
    0xB8FF00,  # +21 °C
    0xB0FF00,  # +22 °C
    0xA8FF00,  # +23 °C
    0xA1FF00,  # +24 °C
    0x99FF00,  # +25 °C
    0x8FFF00,  # +26 °C
    0x80FF00,  # +27 °C
    0x70FF00,  # +28 °C
    0x61FF00,  # +29 °C
    0x52FF00,  # +30 °C
    0x42FF00,  # +31 °C
    0x33FF00,  # +32 °C
    0x2EFF00,  # +33 °C
    0x26FF00,  # +34 °C
    0x1FFF00,  # +35 °C
    0x17FF00,  # +36 °C
    0x0FFF00,  # +37 °C
    0x0AFF00,  # +38 °C
    0x05FF00,  # +39 °C
    0x00FF00  # +40 °C
]

COLORS_INT = [  # temperatura w domu, od 10 °C (21 diod)
    0xFF0000,  # 10 °C
    0xFF1A00,  # 11 °C
    0xFF3300,  # 12 °C
    0xFF4C00,  # 13 °C
    0xFF6600,  # 14 °C
    0xFF8000,  # 15 °C
    0xFF9900,  # 16 °C
    0xFFB200,  # 17 °C
    0xFFCC00,  # 18 °C
    0xFFE600,  # 19 °C
    0xFFFF00,  # 20 °C
    0xE6FF00,  # 21 °C
    0xCCFF00,  # 22 °C
    0xB2FF00,  # 23 °C
    0x99FF00,  # 24 °C
    0x80FF00,  # 25 °C
    0x66FF00,  # 26 °C
    0x4DFF00,  # 27 °C
    0x33FF00,  # 28 °C
    0x19FF00,  # 29 °C
    0x00FF00  # 30 °C
]
