import time
import shutil
import os
import datetime
import smbus
import w1thermsensor

import _rpi_ws281x as ws

import Adafruit_BMP.BMP085 as BMP085 # Pressure sensor library

import colors

import generateHtml

tempIntExact = 0	#Internal temperature float
tempIntExactStr = ""	#Internal temperature string
tempOutExact = 0	#External temperature float
tempExtExactStr = ""	#Exact temperature string
tempIntRound = 0	#Internal temperature rounded to integer
tempOutRound = 0	#External temperature rounded to integer

tempIntArray = [-100.0]*1440	# Internal temperature history
tempOutArray = [-100.0]*1440	# External temperature history
pressureArray = [-100.0]*1440	# Pressure history

altitudeHerning = 58

maskInt = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
maskOut = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


#Internal temperature sensor error
errorInt = 0

#External temperature sensor error
errorOut = 0


# LED configuration.
LED_CHANNEL    = 0
LED_COUNT      = 82         # How many LEDs to light.
LED_FREQ_HZ    = 800000     # Frequency of the LED signal.  Should be 800khz or 400khz.
LED_DMA_NUM    = 10         # DMA channel to use, can be 0-14.
LED_GPIO       = 18         # GPIO connected to the LED signal line.  Must support PWM!
LED_BRIGHTNESS = 50	    # Set to 0 for darkest and 255 for brightest
LED_INVERT     = 0          # Set to 1 to invert the LED signal, good if using NPN
							
LED_COUNT_OUT  = 61
LED_COUNT_INT  = 21

def clearOneByOne():
	for j in range(LED_COUNT_OUT):
		for i in range(LED_COUNT_OUT):
			if i <= j:
				color = 0x000000	
			else:
				color = colors.COLORS_OUT[i] & maskOut[i]
			ws.ws2811_led_set(channel, i, color)
			
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		if maskOut[j] == 0xFFFFFF: 
			time.sleep(0.02)

	offset=LED_COUNT_OUT
	
	for j in range(LED_COUNT_INT):
		for i in range(LED_COUNT_INT):
			if i <= j:
				color = 0x000000	
			else:
				color = colors.COLORS_INT[i] & maskInt[i]
			ws.ws2811_led_set(channel, i+offset, color)
			
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		if maskInt[j] == 0xFFFFFF:
				time.sleep(0.03)
	return

def clearAll():
	for i in range(LED_COUNT):
		color = 0x000000
		ws.ws2811_led_set(channel, i, color)
	resp = ws.ws2811_render(leds)
	if resp != ws.WS2811_SUCCESS:
		message = ws.ws2811_get_return_t_str(resp)
		raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
	return

def displayWhite():
	for j in range(LED_COUNT_OUT):
		for i in range(LED_COUNT_OUT):
			if i <= j:
				color = 0xFFFFFF & maskOut[i]	
				print color
			else:
				color = 0x000000
			ws.ws2811_led_set(channel, i, color)
			
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		if maskOut[j] == 0xFFFFFF: 
			time.sleep(0.02)

	offset=LED_COUNT_OUT
	
	for j in range(LED_COUNT_INT):
		for i in range(LED_COUNT_INT):
			if i <= j:
				color = 0xFFFFFF & maskInt[i]	
			else:
				color = 0x000000
			ws.ws2811_led_set(channel, i+offset, color)
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		if maskInt[j] == 0xFFFFFF:
			time.sleep(0.03)
	return


def colorTest():
	for i in range(LED_COUNT_OUT):
		color = colors.COLORS_OUT[i]
		ws.ws2811_led_set(channel, i, color)
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		time.sleep(0.01)
	offset = 61

	for i in range(LED_COUNT_INT):
		color = colors.COLORS_INT[i]
		ws.ws2811_led_set(channel, i+offset, color)
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		time.sleep(0.03)
	return


def colorRotate():
	global maskOut
	global maskInt
	for k in range (1):
		for j in range(LED_COUNT+1):
			for i in range(LED_COUNT_OUT):
				index = (i + j) % LED_COUNT
				color = colors.COLORS[index] & maskOut[i]
				ws.ws2811_led_set(channel, i, color)
			resp = ws.ws2811_render(leds)
			if resp != ws.WS2811_SUCCESS:
				message = ws.ws2811_get_return_t_str(resp)
				raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
			time.sleep(0.03)

	offset=LED_COUNT_OUT
	
	for k in range (1):
		for j in range(LED_COUNT+1):
			for i in range(LED_COUNT_INT):
				index = (i + j + 61) % LED_COUNT
				color = colors.COLORS[index] & maskInt[i]
				ws.ws2811_led_set(channel, i+offset, color)
			resp = ws.ws2811_render(leds)
			if resp != ws.WS2811_SUCCESS:
				message = ws.ws2811_get_return_t_str(resp)
				raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
			time.sleep(0.05)

	return


def getDateTime():
	now = datetime.datetime.now()
	return str(now)


def getTemperature():
	global tempIntExact
	global tempIntExactStr
	global tempIntRound
	global tempOutExact
	global tempOutExactStr
	global tempIntRound
	global tempIntArray
	global tempOutArray

	#Check if internal temperature sensor is connected
	if not os.path.isfile("/sys/bus/w1/devices/28-0416b377dcff/w1_slave"):
		errorInt = 1
		print "Internal temperature sensor error"
		
	else:
		errorInt = 0
		source = "/sys/bus/w1/devices/28-0416b377dcff/w1_slave"
		destination = "/home/pi/Projekty/Termometr"
		shutil.copy(source, destination)
		os.rename('w1_slave', 'temp_int')

		f = open('temp_int', 'r')
		f.readline()
		f.read(29)
		tempInt = f.read()

		tempIntExact= tempInt[0] + tempInt[1] + '.' + tempInt[2] + tempInt[3] + tempInt[4]
		tempIntExactStr = '+' + str(tempIntExact)
		print tempIntExactStr

		print "Temp exact int: ", str(tempIntExact)

		tempIntRound = int(round(float(tempIntExact)))
		print "Temp rounded: ", str(tempIntRound)

		#Update history
		for i in range(len(tempIntArray) - 1):
			tempIntArray[i] = tempIntArray[i+1]
		tempIntArray[len(tempIntArray)-1] = tempIntExact

		#Clear mask
		for i in range(LED_COUNT_INT):
			maskInt[i] = 0
 
		#Apply new mask
		for i in range(tempIntRound - 9):
			maskInt[i] = 0xFFFFFF

	#Check if external temperature sensor is connected 28-00000a3925cc
	#if not os.path.isfile("/sys/bus/w1/devices/28-0416b389ebff/w1_slave"):
	if not os.path.isfile("/sys/bus/w1/devices/28-00000a3925cc/w1_slave"):
		errorOut = 1
		print "External temperature sensor error"

	else:
		errorOut = 0
		source = "/sys/bus/w1/devices/28-00000a3925cc/w1_slave"
		destination = "/home/pi/Projekty/Termometr"
		shutil.copy(source, destination)
		os.rename('w1_slave', 'temp_out')

		f = open('temp_out', 'r')
		f.readline()
		f.read(29)

		#Check sign
		sign = f.read(1)
		if sign[0] == '-':
			print "Negative"
			signExt = '-'
		else:
			print "Positive"
			signExt = '+'

		f.close()

		#Reopen and read temperature
		f = open('temp_out', 'r')
		f.readline()
		if signExt == '-':
			f.read(30)
			tempOut = f.read()
		else:
			f.read(29)
			tempOut = f.read()

		strlen = len(tempOut)

		if strlen == 4:	#below 1 degree
			if signExt == '-':
				tempOutExact = '-' + '0' + '.' + tempOut
			else:
				tempOutExact = '0' + '.' + tempOut
		elif strlen == 5: #between 1 and 10
			if signExt == '-':
				tempOutExact = '-' + tempOut[0] + '.' + tempOut[1] + tempOut[2] + tempOut[3]
			else:
				tempOutExact = tempOut[0] + '.' + tempOut[1] + tempOut[2] + tempOut[3]
		elif strlen == 6: #10 and above
			if signExt == '-':
				tempOutExact = '-' + tempOut[0] + tempOut[1] + '.' + tempOut[2] + tempOut[3] + tempOut[4]
			else:
				tempOutExact = tempOut[0] + tempOut[1] + '.' + tempOut[2] + tempOut[3] + tempOut[4]
		

		print "Temp exact ext: ", tempOutExact
		if signExt == '+':
			tempOutExactStr = '+' + str(tempOutExact)
		else:
			tempOutExactStr = str(tempOutExact)
		#print "test" + tempOutExactStr
		tempOutRound = int(round(float(tempOutExact)))
		print "Temp rounded ext: ", tempOutRound

		#Update history
		for i in range(len(tempOutArray) - 1):
			tempOutArray[i] = tempOutArray[i+1]
		tempOutArray[len(tempOutArray)-1] = tempOutExact

		#Clear mask
		for i in range(LED_COUNT_OUT):
			maskOut[i] = 0
 
		#Apply new mask
		for i in range(tempOutRound+21):
			maskOut[i] = 0xFFFFFF

	return

def displayTempNormal():
	global maskOut
	global maskInt
	for i in range(LED_COUNT_OUT):
		color = colors.COLORS_OUT[i] & maskOut[i]
		ws.ws2811_led_set(channel, i, color)
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		time.sleep(0.05)

	#Inner temperature
	offset=61
	
	for i in range(LED_COUNT_INT):
		# Pick a color based on LED position and an offset for animation.
		color = colors.COLORS_INT[i] & maskInt[i]
		# Set the LED color buffer value.
		ws.ws2811_led_set(channel, (i + offset), color)

		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))

		time.sleep(0.05)
	return

def displayTempWhite():
	global maskOut
	global maskInt
	for i in range(LED_COUNT_OUT):
		color = (0xFFFFFF) & (maskOut[i])
		ws.ws2811_led_set(channel, i, color)
		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		if maskOut[i] == 0xFFFFFF:
			time.sleep(0.05)
	

	#Inner temperature
	offset=61
	
	for i in range(LED_COUNT_INT):
		# Pick a color based on LED position and an offset for animation.
		color = (0xFFFFFF) & (maskInt[i])
		# Set the LED color buffer value.
		ws.ws2811_led_set(channel, (i + offset), color)

		resp = ws.ws2811_render(leds)
		if resp != ws.WS2811_SUCCESS:
			message = ws.ws2811_get_return_t_str(resp)
			raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
		if maskInt[i] == 0xFFFFFF:
			time.sleep(0.05)	
	return

def generateHtmlSipmle():
    sensor = w1thermsensor.W1ThermSensor()
    temp = sensor.get_temperature()
    now = datetime.datetime.now()
    myFile = open("/var/www/html/index.html", "w")
    myFile.write(str(now)+": "+str(temp))
    myFile.close()    
    return

# Create a ws2811_t structure from the LED configuration.
# Note that this structure will be created on the heap so you need to be careful
# that you delete its memory by calling delete_ws2811_t when it's not needed.
leds = ws.new_ws2811_t()

# Initialize all channels to off
for channum in range(2):
    channel = ws.ws2811_channel_get(leds, channum)
    ws.ws2811_channel_t_count_set(channel, 0)
    ws.ws2811_channel_t_gpionum_set(channel, 0)
    ws.ws2811_channel_t_invert_set(channel, 0)
    ws.ws2811_channel_t_brightness_set(channel, 0)

channel = ws.ws2811_channel_get(leds, LED_CHANNEL)

ws.ws2811_channel_t_count_set(channel, LED_COUNT)
ws.ws2811_channel_t_gpionum_set(channel, LED_GPIO)
ws.ws2811_channel_t_invert_set(channel, LED_INVERT)
ws.ws2811_channel_t_brightness_set(channel, LED_BRIGHTNESS)

ws.ws2811_t_freq_set(leds, LED_FREQ_HZ)
ws.ws2811_t_dmanum_set(leds, LED_DMA_NUM)

# Initialize library with LED configuration.
resp = ws.ws2811_init(leds)
if resp != ws.WS2811_SUCCESS:
	message = ws.ws2811_get_return_t_str(resp)
	raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, message))

#Pressure sensor
#sensor = BMP085.BMP085()

# Main loop:
try:
	while True:
		
		clearAll()
		#colorTest()
		generateHtmlSipmle()
		sensor = w1thermsensor.W1ThermSensor()
                temp = float(sensor.get_temperature())
                print(temp)
                temp=int(round(temp))
                print(temp)
                display_temp=21+temp
		for i in range(display_temp):
                    color = colors.COLORS_OUT[i]
                    ws.ws2811_led_set(channel, i, color)
                    resp = ws.ws2811_render(leds)
                    if resp != ws.WS2811_SUCCESS:
                            message = ws.ws2811_get_return_t_str(resp)
                            raise RuntimeError('ws2811_render failed with code {0} ({1})'.format(resp, message))
                    time.sleep(0.01)
		#getTemperature()
		#displayTempWhite()
		#time.sleep(0.5)
		#colorRotate()
		#getPressure()
		#colorTest()

		#generateHtml.generateHtml(tempIntExactStr, tempOutExactStr, tempIntArray, tempOutArray, pressureArray)
		time.sleep(60)

		




finally:
	ws.ws2811_fini(leds)
	ws.delete_ws2811_t(leds)

