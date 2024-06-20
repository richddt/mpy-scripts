import seesaw
from tween import tween
from machine import Pin


class RotaryEncoder(object):
    BaseAddr = 0x36
    ButtonPin = 24

    def __init__(self, i2c, addr=0, initial_value=0.5, clicks=24, wraparound=False):
        self._seesaw = seesaw.Seesaw(i2c, RotaryEncoder.BaseAddr + addr)
        self._value = tween(initial_value, initial_value, 0.2)
        self._delta = 1.0 / clicks
        self._started = False
        self._wraparound = wraparound

    async def start(self):
        await self._seesaw.start()
        self._seesaw.pin_mode(RotaryEncoder.ButtonPin, seesaw.Seesaw.INPUT_PULLUP)
        self._position = await self._seesaw.encoder_position()
        self._position = -self._position
        self._button = await self._seesaw.digital_read(24)
        self._started = True

    async def tick(self):
        if not self._started:
            return
        new_position = await self._seesaw.encoder_position()
        new_position = -new_position
        if new_position != self._position:
            new_value = (
                self._value.target + (new_position - self._position) * self._delta
            )
            if self._wraparound:
                if new_value < 0.0:
                    new_value += 1.0
                elif new_value > 1.0:
                    new_value -= 1.0
            else:
                new_value = min(1.0, max(0.0, new_value))
                self._value.tween(new_value, 0.1)
            self._position = new_position

        # new_button = await self._seesaw.digital_read(24)
        # if new_button != self._button:
        #     self._button = new_button
        #     if new_button == 0:
        #         print("Button pressed")

    @property
    def value(self):
        return self._value


class RotarySwitch(object):
    def __init__(self, pins):
        self.state = 0
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for p, v in pins]
        self.values = [v for p, v in pins]
        self._value = self.values[0]

    def tick(self):
        for i, p in enumerate(self.pins):
            if p.value() == 0:
                self._value = self.values[i]

    @property
    def value(self):
        return self._value
