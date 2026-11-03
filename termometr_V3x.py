import subprocess
import time
from rpi_ws281x import *
from ds18B20 import *
from colors import *
from aurora import *
from datetime import datetime

tempDS18B20 = 0
tempAqara = 0



# LED strip configuration:
LED_COUNT      = 82      # Number of LED pixels.
LED_COUNT_EXT  = 61
LED_COUNT_INT  = 21
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
        #time.sleep(wait_ms/1000.0)

def displayTempNormal(strip, tempExt, tempInt):
    wait_ms=50
    maskInt = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    maskExt = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    for i in range(tempInt-9): #Internal termperature display starts at 10
        maskInt[i] = 0xFFFFFF
    
    for i in range(tempExt+21): #Assuming positive temperature. External temperature display starts at -20
        maskExt[i] = 0xFFFFFF
    
    for i in range(LED_COUNT_EXT):
        color = COLORS_EXT[i] & maskExt[i]        
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


    #Inner temperature
    offset=61

    for i in range(LED_COUNT_INT):
        color = COLORS_INT[i] & maskInt[i]
        strip.setPixelColor((i+offset), color)
        strip.show()
        time.sleep(wait_ms/1000.0)


    return

def colorTest(strip):
    for i in range(LED_COUNT_EXT):
        color = COLORS_EXT[i]
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(0.01)
    offset = 61

    for i in range(LED_COUNT_INT):
        color = COLORS_INT[i]
        strip.setPixelColor((i+offset), color)
        strip.show()
        time.sleep(0.03)
    return

#sudo journalctl -u zigbee2mqtt.service -f


try:
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    while True:        
                
        tempDS18B20 = getTempDS18B20()
        if getTempAurora() != -1:
            tempAqara = getTempAurora()
        clearAll(strip)
        time.sleep(2)
        
        displayTempNormal(strip, round(tempAqara), round(tempDS18B20))

        now = datetime.now()

        current_time = now.strftime("%H:%M:%S")
        print("Current Time =", current_time)

        print("The DS18B20 temperature is %s celsius" % tempDS18B20)
        print("The Aqara temperature is %s celsius" % tempAqara)     
        
        time.sleep(10)

except KeyboardInterrupt:
        colorWipe(strip, Color(0,0,0), 10)
