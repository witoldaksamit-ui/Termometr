import subprocess
import time
from datetime import datetime
import psutil

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

# Define the command to execute
cmd = "sudo journalctl -u zigbee2mqtt.service -f"

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    # Open a file to write the command output to
    with open('output.log', 'w') as f:
        # Execute the command and redirect its output to the file
        proc = subprocess.Popen(cmd, shell=True, stdout=f)
        time.sleep(2)
        # Wait for the command to finish executing
        kill(proc.pid)
    
    time.sleep(2)

# The command has now finished executing and its output has been written to the file
print("Command finished executing")
