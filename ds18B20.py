import time
from w1thermsensor import W1ThermSensor

def getTempDS18B20():
    sensor = W1ThermSensor()
    temperature = sensor.get_temperature()    
    return temperature