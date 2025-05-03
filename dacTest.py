import adafruit_mcp4725
import board
import busio
import time
import random


i2c = busio.I2C(board.SCL,board.SDA)
dac = adafruit_mcp4725.MCP4725(i2c,address=0x65)

while True:
    try:
        user_input = input("\nEnter new value 0-55500\n")
        number = int(user_input)
        dac.value = number

        
    except KeyboardInterrupt:
        print("goodbye")
        break