
import fern
from machine import Pin
from time import ticks_ms, ticks_diff, sleep_ms

MAGNET_DURATION_MS = 15000 # hold duration in ms, 75000 default (1min 15sec)
DEBOUNCE_MS = 40

magnet = Pin(fern.D8, Pin.OUT, value=0)
button = Pin(fern.D4, Pin.IN, Pin.PULL_UP)

print("ShiBarbie initializing...")
sleep_ms(1000)

last_reading = button.value()
stable = last_reading
last_change = ticks_ms()

armed = False
active = False
start_time = 0

print("ShiBarbie ready")

try:
    while True:
        now = ticks_ms()
        reading = button.value()

        if reading != last_reading:
            last_change = now
            last_reading = reading

        if ticks_diff(now, last_change) >= DEBOUNCE_MS:
            stable = reading

        if not active:
            if stable == 0:
                armed = True
            elif armed and stable == 1:
                armed = False
                active = True
                start_time = now
                magnet.on()
                print("Magnet ON")

        elif ticks_diff(now, start_time) >= MAGNET_DURATION_MS:
            magnet.off()
            active = False
            print("Magnet OFF")

        sleep_ms(10)

finally:
    magnet.off()
    print("Stopped - Magnet OFF")
