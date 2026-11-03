from subprocess import Popen, PIPE

cmd = "sudo journalctl -u zigbee2mqtt.service -f"
proc = Popen(cmd, shell=True, stdout=PIPE)
while True:
   output = proc.stdout.readline()
   if output == "" and proc.poll() is not None:
       break
   if output:
       # parse line, if its temperature, write to file
       print(output.strip())
rc = proc.poll()