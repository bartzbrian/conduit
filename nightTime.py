import nltk
import openai
from openai import OpenAI

from datetime import datetime
from suntime import Sun, SunTimeException
from os import kill
from os import getpid
from signal import SIGKILL
import time
import random
import requests
import serial
import subprocess
import os
import glob
from PIL import Image

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY",""))

files = glob.glob('/home/pi/Desktop/conduit/img/*')
for f in files:
    os.remove(f)

import adafruit_thermal_printer

uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=3000)
ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)
printer = ThermalPrinter(uart)

imgNum = 0

latitude = 37.7749
longitude = -122.4194
sun = Sun(latitude, longitude)
sr = sun.get_local_sunrise_time()
print("set to self destruct this process at:")
print(sr.time())

with open('/home/pi/Desktop/conduit/daily-transmission.txt', 'r') as file:
    data = file.read().replace('\n', '')

is_noun = lambda pos: pos[:2] == 'NN'
tokenized = nltk.word_tokenize(data)
nouns = [word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)]
print("nouns:")
print(nouns)

tags = nltk.pos_tag(data.split(' '))
adjectives = [w for w, t in tags if t == 'JJ']
print('adjectives')
print(adjectives)

newDay = False
currTime = datetime.now()
prevTime = currTime

while True:
    currTime = datetime.now()

    if len(adjectives) != 0 and len(nouns) != 0:
        currentQuery = random.choice(adjectives) + ' ' + random.choice(nouns)
        print(currentQuery)

        if prevTime.day != currTime.day:
            sr = sun.get_local_sunrise_time()
            print("a new day has dawned")
            currentTime = datetime.now()
            print(currentTime.time())
            newDay = True

        # Try generating an image, retry immediately on content policy violation
        while True:
            try:
                response = client.images.generate(
                    model="dall-e-2",
                    prompt=currentQuery,
                    n=1,
                    size="256x256",
                    response_format="url",
                )
                image_url = response.data[0].url
                print(image_url)
                break  # success, break out of retry loop
            except openai.BadRequestError as e:
                print("Bad request error:", e)
                print("Likely content policy violation. Retrying with new prompt...")
                currentQuery = random.choice(adjectives) + ' ' + random.choice(nouns)
                continue
            except openai.OpenAIError as e:
                print("OpenAI API error:", e)
                continue

        # Save image
        img_data = requests.get(image_url).content
        title = f'/home/pi/Desktop/conduit/img/{imgNum}.jpg'
        with open(title, 'wb') as handler:
            handler.write(img_data)

        # Print image
        if printer.has_paper():
            print("printing: " + currentQuery)
            printCommand = "lp -o fit-to-page " + title
            process = subprocess.Popen(printCommand.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            time.sleep(10)
            printer.feed(3)

        imgNum += 1

        if (currTime.time() > sr.time() and newDay):
            print("sun has risen, time to die")
            pid = getpid()
            kill(pid, SIGKILL)

        print('printed image, waiting 45 minutes for a new dream')
        time.sleep(2700)

    prevTime = currTime