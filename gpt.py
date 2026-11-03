import subprocess
import time
from datetime import datetime
import psutil

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
#proc = Popen(cmd, shell=True, stdout=PIPE)



while True:
    # Define the command to execute
    cmd = "sudo journalctl -u zigbee2mqtt.service -n 10 -f"
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    # Open a file to write the command output to
    with open('output.log', 'w') as f:
        # Execute the command and redirect its output to the file
        proc = subprocess.Popen(cmd, shell=True, stdout=f)
        #subprocess.run(cmd, shell=True, stdout=f, timeout=10)

        
        #try:
            # Wait for the command to run for 10 seconds
        time.sleep(3)
            
        #kill(proc.pid)
        #finally:
            # Terminate the command after 10 seconds
            #proc.send_signal(subprocess.signal.SIGKILL)
            #proc.send_signal(subprocess.signal.SIGINT)

        # Terminate the command after 10 seconds
        proc.kill()

    # Wait for a short time before running the command again
    time.sleep(2)
