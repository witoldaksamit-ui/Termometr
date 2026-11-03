import subprocess
import time
from datetime import datetime
import psutil

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def getTempAurora():
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    #print("Current Time =", current_time)
    # Open a file to write the command output to
    cmd = "sudo journalctl -u zigbee2mqtt.service -f"
    with open('output.log', 'w') as f:
        # Execute the command and redirect its output to the file
        proc = subprocess.Popen(cmd, shell=True, stdout=f)
        time.sleep(2)
        # Wait for the command to finish executing
        kill(proc.pid)
    
    f.close()

    with open('output.log', 'r') as f:
        single_line = ''
        for line in f:
            single_line += line.strip()
            
    f.close()

    search_word = 'temperature'
    last_pos = single_line.rfind(search_word)
    if last_pos != -1:
        #print(f"Last occurrence of '{search_word}' is at position {last_pos+1}.")
        extracted_text = single_line[last_pos:]

        #print(extracted_text)

        char = ','
        first_index = extracted_text.index(char)
        #print(f"The first occurrence of '{char}' is at index {first_index}.")
        temperature = extracted_text[13:first_index]

        #print(temperature)

        temp = float(temperature)
        #print ('Aurora: ')
        #print(rounded_temp)
        
        return temp
    else:
        return -1
        print(f"'{search_word}' not found in text.")


