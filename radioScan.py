import adafruit_mcp4725
import board
import busio
from datetime import datetime
from suntime import Sun, SunTimeException
from os import kill
from os import getpid
from signal import SIGKILL
import time
import random

latitude = 37.7749
longitude = -122.4194
sun = Sun(latitude,longitude)
ss = sun.get_local_sunset_time()
print("set to self destruct this process at:")
print(ss.time())

i2c = busio.I2C(board.SCL,board.SDA)
dac = adafruit_mcp4725.MCP4725(i2c,address=0x65)

#initialize lastLine and prevLine
with open("/home/pi/Desktop/conduit/daily-transmission.txt") as f:
    line = ''
    for line in f:
        pass
    lastLineCurr = line
    lastLinePrev = line

currentDAC = random.randrange(1,55500)
dac.value = currentDAC

while True:
    
    currTime = datetime.now()

    #  self destruct at sunset
    if currTime.time() > ss.time():
        print("sun has set, time to die")
        pid = getpid()
        kill(pid,SIGKILL)

    #if the dac value is near its max randomize it
    if currentDAC > 55500:
        print("max range reached, randomizing frequency")
        currentDAC = random.randrange(1,55500)
    #else if the dac value is in range, advance it
    else:
        time.sleep(.03)
        currentDAC = currentDAC + 1
        dac.value = currentDAC

    #update lastLine as the most recent last line of text
    with open("/home/pi/Desktop/conduit/daily-transmission.txt") as f:
        for line in f:
            pass
        lastLineCurr = line

    # if there's a new line of text (i.e. there are voices playing on the radio)
    if lastLineCurr != lastLinePrev:

        print('voices detected, pausing for 20 seconds')

        #sit on this frequency for 30 seconds
        time.sleep(30)
        lastLinePrev = lastLineCurr

        #switch to random frequency before proceeding
        print("randomizing frequency")
        print((currentDAC/2775)+88)        
        currentDAC = random.randrange(1,55500)
        time.sleep(3)





    

