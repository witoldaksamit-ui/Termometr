import subprocess
import time
from rpi_ws281x import *
from ds18B20 import *
from colors import *
from aurora import *
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import argparse

import urllib
import urllib.request
#import html2text
import os
from github import Github, Auth

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

def htmlPush(tempDS18B20, tempAqara)  :
    # 1. Get the current date and time
    now = datetime.now()
    # Format it for readability (e.g., Friday, January 16, 2026 01:53 PM)
    formatted_time = now.strftime("%A, %B %d, %Y %I:%M %p")

    # 2. Define the HTML structure with the time injected
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Current Time Report</title>
    </head>
    <body>
        <p><strong>{formatted_time}</strong></p>
        <p><strong>Temperatura w domu: {tempDS18B20}</strong></p>
        <p><strong>Temperatura na zewnątrz: {tempAqara}</strong></p>
        <p><strong>Marek &Aksamit.com@.PL$.XD.%ro.*D.NL.CN*.JP</strong></p>
    </body>
    </html>
    """
    
    # 1. Setup Authentication
    ACCESS_TOKEN = "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"
    REPO_NAME = "witoldaksamit-ui/velvethome.github.io"

    FILE_PATH = "index.html"  # Path to the file in the repo

    g = Github(ACCESS_TOKEN)
    repo = g.get_repo(REPO_NAME)

    def update_github_file():
        try:
            # 2. Pull the file content
            # This retrieves the file metadata, including its current SHA hash
            contents = repo.get_contents(FILE_PATH, ref="main")
            
            # Decode the existing content from bytes
            original_content = contents.decoded_content.decode("utf-8")
            print(f"Current content: {original_content}")

            # 3. Modify the content
            new_content = html_content

            # 4. Commit and Push back to GitHub
            # You must provide the file's current SHA to update it
            repo.update_file(
                path=contents.path,
                message="Automated update from Python script",
                content=new_content,
                sha=contents.sha,
                branch="main"
            )
            
            print("Successfully committed and pushed changes.")

        except Exception as e:
            print(f"An error occurred: {e}")

    if __name__ == "__main__":
        update_github_file()
    
    return
    
    
def current_utc_iso_z() -> str:
    # produce ISO 8601 with seconds precision and 'Z' for UTC
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def append_timestamp(outfile: str) -> None:
    ts = current_utc_iso_z()
    # Append the timestamp as a new last line (create file if missing)
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(ts + "\n")


def txtPush(tempDS18B20, tempAqara, current_time)  :
    # 1. Get the current date and time
    now_utc = datetime.now(timezone.utc)
    now_cet = now_utc.astimezone(ZoneInfo("Europe/Warsaw"))
    now = now_cet.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    # Format it for readability (e.g., Friday, January 16, 2026 01:53 PM)
    #formatted_time = now.strftime("%A, %B %d, %Y %I:%M %p")

    
    # 1. Setup Authentication
    ACCESS_TOKEN = "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"
    REPO_NAME = "witoldaksamit-ui/velvethome.github.io"

    FILE_PATH = "temperatures.txt"  # Path to the file in the repo
    FILE_PATH_GARMIN = "monkey.txt"  # Path to the file in the repo

    g = Github(ACCESS_TOKEN)
    repo = g.get_repo(REPO_NAME)

    def update_github_file():
        try:
            # 2. Pull the file content
            # This retrieves the file metadata, including its current SHA hash
            contents = repo.get_contents(FILE_PATH, ref="main")
            
            # Decode the existing content from bytes
            original_content = contents.decoded_content.decode("utf-8")
            #print(f"Current content: {original_content}")
            
            # 1. Pobierz i zdekoduj treść (dostaniesz bytes, więc używamy decode('utf-8'))
            #file_content_string = original_content.decoded_content.decode('utf-8')

            # 2. Podziel na linie
            lines = original_content.splitlines()

            # 3. Pobierz liczbę linii
            num_lines = len(lines)
            print(num_lines)
            # 4. Usuń pierwszą linię, jeśli warunek jest spełniony (> 800)
            if num_lines > 800:
                lines.pop(0)
                
            # Połącz linie z powrotem w jeden string
            new_content = "\n".join(lines)
            
            # 3. Modify the content
            new_content_updated = new_content + "\n" + now + "," + str(tempDS18B20) + "," + str(tempAqara)

            # 4. Commit and Push back to GitHub
            # You must provide the file's current SHA to update it
            repo.update_file(
                path=contents.path,
                message="Automated update from Python script",
                content=new_content_updated,
                sha=contents.sha,
                branch="main"
            )
            
            print("Successfully committed and pushed changes.")
            
             # 2. Pull the file content
            # This retrieves the file metadata, including its current SHA hash
            contents = repo.get_contents(FILE_PATH_GARMIN, ref="main")
        
                           
            # 3. Modify the content
            new_content_updated = str(tempDS18B20) + "\n" + str(tempAqara) + "\n" + current_time

            # 4. Commit and Push back to GitHub
            # You must provide the file's current SHA to update it
            repo.update_file(
                path=contents.path,
                message="Automated update from Python script",
                content=new_content_updated,
                sha=contents.sha,
                branch="main"
            )
            print("Successfully committed and pushed changes Garmin.")

        except Exception as e:
            print(f"An error occurred: {e}")

    if __name__ == "__main__":
        update_github_file()
    
    return
        
while True:
    try:
        strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()
        i = 0
        
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
            
            #htmlPush(tempDS18B20, tempAqara)   
            
            i = i+1
            print(i)
            if(i > 7):
                txtPush(tempDS18B20, tempAqara, current_time)  
                print("Temp sent")
                i = 0
            
            time.sleep(10)
            

    except KeyboardInterrupt:
            colorWipe(strip, Color(0,0,0), 10)
            
    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        print("Restartowanie za 5 sekund...")
        time.sleep(5)  # Przerwa przed restartem, aby uniknąć zapętlenia błędów
