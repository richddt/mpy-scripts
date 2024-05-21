import time


class tween(object):
    def __init__(self, value=0.0, target=0.0, dt=0.0, min=0.0, max=1.0):
        self._value = float(value)
        self._target = float(target)
        self.tween(target, dt)

    def tween(self, target, dt):
        self._value = float(self)
        self._target = float(target)
        self.dt = dt * 1000.0
        self.start_time = time.ticks_ms()

    def __float__(self):
        if self._target == self._value:
            return self._target
        progress = time.ticks_diff(time.ticks_ms(), self.start_time) / self.dt
        if progress > 1.0:
            self._value = self._target
            return self._target
        else:
            return self._value + (self._target - self._value) * progress

    @property
    def value(self):
        return float(self)

    @property
    def target(self):
        return self._target

    def __repr__(self):
        return str(float(self))
