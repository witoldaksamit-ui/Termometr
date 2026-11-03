import subprocess
import time

#sudo journalctl -u zigbee2mqtt.service -f


try:

    
    while True:

        #cmd = "sudo journalctl -u zigbee2mqtt.service -f"
        #process = subprocess.Popen(cmd)
        process = subprocess.Popen(['sudo', 'journalctl', '-n', '10', '-u', 'zigbee2mqtt.service', '-f'])#, '--no-tail'])

        time.sleep(1)
        process.kill()

        time.sleep(2)
        
except KeyboardInterrupt:
    print("End")
