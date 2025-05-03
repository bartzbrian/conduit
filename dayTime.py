import pyaudio
import websockets
import asyncio
import base64
import json
import board
import busio
import time
import serial
import random
from datetime import datetime
from suntime import Sun
from os import kill, getpid
from signal import SIGKILL
import adafruit_thermal_printer

latitude = 37.7749
longitude = -122.4194
sun = Sun(latitude, longitude)
ss = sun.get_local_sunset_time()
print("set to self destruct this process at:")
print(ss.time())

uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=3000)
ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)
printer = ThermalPrinter(uart)

printer.print("WAKING UP")
printer.feed(3)

auth_key = ''

FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)

URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

async def send(ws):
    while True:
        try:
            data = stream.read(FRAMES_PER_BUFFER)
            data = base64.b64encode(data).decode("utf-8")
            json_data = json.dumps({"audio_data": str(data)})
            await ws.send(json_data)
        except websockets.exceptions.ConnectionClosedError as e:
            print(e)
            break
        except Exception as e:
            print(f"Unexpected send error: {e}")
            break
        await asyncio.sleep(0.01)

async def receive(ws):
    while True:
        currTime = datetime.now()

        if currTime.time() > ss.time():
            print("time to die")
            printer.feed(2)
            printer.print("GOING TO SLEEP")
            printer.feed(3)
            pid = getpid()
            kill(pid, SIGKILL)

        try:
            result_str = await ws.recv()
            text = json.loads(result_str)['text']
            if "." in text:
                print(text)
                with open('/home/pi/Desktop/conduit/daily-transmission.txt', 'a+') as f:
                    f.write(text)
                if printer.has_paper():
                    printer.print(text)
                    if random.randrange(1, 10) > 6:
                        printer.feed(1)
        except websockets.exceptions.ConnectionClosedError as e:
            print(e)
            break
        except Exception as e:
            print(f"Unexpected receive error: {e}")
            break

async def send_receive():
    while True:
        try:
            print(f'Connecting websocket to URL: {URL}')
            async with websockets.connect(
                URL,
                extra_headers=(("Authorization", auth_key),),
                ping_interval=5,
                ping_timeout=20
            ) as ws:
                print("Connected. Waiting for session start...")
                session_begins = await ws.recv()
                print(session_begins)

                send_task = asyncio.create_task(send(ws))
                receive_task = asyncio.create_task(receive(ws))

                done, pending = await asyncio.wait(
                    [send_task, receive_task],
                    return_when=asyncio.FIRST_EXCEPTION
                )
                for task in pending:
                    task.cancel()

        except Exception as e:
            print(f"Connection error or unexpected exception: {e}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)

async def main():
    try:
        await send_receive()
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
