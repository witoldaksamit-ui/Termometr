import subprocess
import time
from rpi_ws281x import *
from ds18B20 import *
from colors import *
#from w1thermsensor import W1ThermSensor

# LED strip configuration:
LED_COUNT      = 82      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 20     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53



# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)
 
def clearAll(strip):
    color = 0x000000
    wait_ms=50
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)




#sudo journalctl -u zigbee2mqtt.service -f


try:
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    while True:        
        
        print ('Color wipe animations.')
        colorWipe(strip, Color(137, 83, 237))  # Red wipe

        time.sleep(5)
        
        clearAll(strip)

except KeyboardInterrupt:
        colorWipe(strip, Color(0,0,0), 10)
