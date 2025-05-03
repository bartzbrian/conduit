import datetime
from suntime import Sun, SunTimeException
import RPi.GPIO as GPIO
import os
import sys
import subprocess
import glob
import time
import traceback  # For detailed error logs

# Path for logging errors
ERROR_LOG_PATH = "/home/pi/Desktop/conduit/error_log.txt"

# Clear the log once when script starts
open(ERROR_LOG_PATH, "w").close()

# Define GPIO pins
redPin = 35
bluePin = 32
greenPin = 33

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)

redPWM = GPIO.PWM(redPin, 1000)
greenPWM = GPIO.PWM(greenPin, 1000)
bluePWM = GPIO.PWM(bluePin, 1000)

redPWM.start(0)
greenPWM.start(0)
bluePWM.start(0)

# Set latitude & longitude
latitude = 37.7749
longitude = -122.4194
sun = Sun(latitude, longitude)
sr = sun.get_local_sunrise_time()
ss = sun.get_local_sunset_time()

# Functions to control LED color
def dayLED():
    bluePWM.ChangeDutyCycle(100)
    redPWM.ChangeDutyCycle(60)
    greenPWM.ChangeDutyCycle(75)

def nightLED():
    bluePWM.ChangeDutyCycle(0)
    redPWM.ChangeDutyCycle(35)
    greenPWM.ChangeDutyCycle(100)

# Functions to clear text & images
def clearText():
    open("/home/pi/Desktop/conduit/daily-transmission.txt", "w").close()

def clearImg():
    files = glob.glob('/home/pi/Desktop/conduit/img/*')
    for f in files:
        os.remove(f)

print("Starting code. The time is:")
clearText()
prevTime = datetime.datetime.now()
print(prevTime)
dayTime = False
nightTime = False
print("sunrise:", sr)
print("sunset:", ss)

idlePrinted = False

# Main loop
while True:
    try:
        currentTime = datetime.datetime.now()
        weekday = currentTime.weekday()  # 0 = Monday, 6 = Sunday

        # Update sunrise/sunset on new day
        if prevTime.day != currentTime.day:
            sr = sun.get_local_sunrise_time()
            ss = sun.get_local_sunset_time()
            print("A new day has dawned:", currentTime.time())
            idlePrinted = False

        # Run only on Friday (4), Saturday (5), Sunday (6) Monday (0)
        if weekday in [0, 4, 5, 6]:  
            if sr.time() < currentTime.time() < ss.time():
                if not dayTime:
                    clearText()
                    dayLED()
                    print("Activating Daytime Code:", currentTime.time())
                    nightTime = False
                    dayTime = True
                    with open(ERROR_LOG_PATH, "a") as errlog:
                        timestamp = f"\n[{datetime.datetime.now()}] Starting dayTime.py and radioScan.py\n"
                        errlog.write(timestamp)
                        subprocess.Popen(['python3', '/home/pi/Desktop/conduit/dayTime.py'], stderr=errlog)
                        subprocess.Popen(['python3', '/home/pi/Desktop/conduit/radioScan.py'], stderr=errlog)

            elif currentTime.time() > ss.time() or currentTime.time() < sr.time():
                if not nightTime:
                    clearImg()
                    nightLED()
                    print("Activating Nighttime Code:", currentTime.time())
                    dayTime = False
                    nightTime = True
                    with open(ERROR_LOG_PATH, "a") as errlog:
                        timestamp = f"\n[{datetime.datetime.now()}] Starting nightTime.py\n"
                        errlog.write(timestamp)
                        subprocess.Popen(['python3', '/home/pi/Desktop/conduit/nightTime.py'], stderr=errlog)

        else:
            if not idlePrinted:
                print("Idle. Today is not a weekend day.")
                idlePrinted = True

        prevTime = currentTime
        time.sleep(5)

    except Exception:
        with open(ERROR_LOG_PATH, "a") as f:
            f.write(f"\n[{datetime.datetime.now()}] ERROR in main loop:\n")
            traceback.print_exc(file=f)
        time.sleep(10)
