"""
Minimal OLED display test – identical I²C wiring as main.py
"""

from machine import I2C, Pin
import ssd1306
import time

# Same bus as main.py
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)

print("I²C scan:", i2c.scan())

# Instantiate display with same parameters as main.py
display = ssd1306.SSD1306_I2C(128, 32, i2c)

# Simple test sequence
display.poweron()
display.fill(0)
display.text("Test 1", 0, 0)
display.show()
time.sleep(1)

display.fill(0)
display.text("Test 2", 0, 12)
display.show()
time.sleep(1)

display.fill(1)   # all pixels on
display.show()
time.sleep(1)

display.fill(0)   # clear
display.show()

print("Display test complete.")
