"""Explicit, unloaded servo calibration. Importing does not initialize hardware.

start() enables PWM at zero duty (no positioning pulses). goto() explicitly
establishes a commanded position; move() requires that position in this session.
Commanded position is never a measurement of physical position.
"""

import json
import os
from time import sleep_ms

MIN_US = 700
MAX_US = 2500
_DEFAULTS = {
    'RELEASE_US': 700,
    'ENGAGE_US': 2000,
    'TIGHTEN_STEP_US': 10,
    'TIGHTEN_INTERVAL_MS': 50,
    'RELEASE_STEP_US': 20,
    'RELEASE_INTERVAL_MS': 30,
    'ENGAGE_CROSSOVER_US': 1600,
    'FAST_TIGHTEN_STEP_US': 20,
    'FAST_TIGHTEN_INTERVAL_MS': 30,
    'MAX_ENGAGEMENT_MS': 15000,
}
_directory = __file__.rsplit('/', 1)[0] if '/' in __file__ else '.'
_CONFIG = _directory + '/servo_config.json'
_pwm = None
_last_us = None


def _integer(value, name, minimum, maximum=None):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    if maximum is not None and value > maximum:
        raise ValueError(name + ' must be <= ' + str(maximum))
    return value


def _position(us):
    return _integer(us, 'pulse width', MIN_US, MAX_US)


def _validate(settings):
    if not isinstance(settings, dict) or set(settings) != set(_DEFAULTS):
        raise ValueError('Configuration must contain exactly the supported settings')
    _position(settings['RELEASE_US'])
    _position(settings['ENGAGE_US'])
    if settings['ENGAGE_US'] <= settings['RELEASE_US']:
        raise ValueError('ENGAGE_US must be greater than RELEASE_US')
    _position(settings['ENGAGE_CROSSOVER_US'])
    if not settings['RELEASE_US'] <= settings['ENGAGE_CROSSOVER_US'] <= settings['ENGAGE_US']:
        raise ValueError('ENGAGE_CROSSOVER_US must be within calibrated endpoints')
    for key in ('TIGHTEN_STEP_US', 'RELEASE_STEP_US', 'FAST_TIGHTEN_STEP_US'):
        _integer(settings[key], key, 1, MAX_US - MIN_US)
    for key in ('TIGHTEN_INTERVAL_MS', 'RELEASE_INTERVAL_MS', 'FAST_TIGHTEN_INTERVAL_MS'):
        _integer(settings[key], key, 1)
    # Keep the duration within the existing bench-test window and safely
    # within the ticks_diff comparison range.
    _integer(settings['MAX_ENGAGEMENT_MS'], 'MAX_ENGAGEMENT_MS', 1, 30000)


def _load():
    try:
        with open(_CONFIG, 'r') as stream:
            settings = json.load(stream)
    except OSError as exc:
        if exc.args and exc.args[0] == 2:  # Missing file only.
            return dict(_DEFAULTS)
        raise
    _validate(settings)
    return settings


_settings = _load()


def start():
    """Initialize GPIO3 PWM with no pulses; never command a stored position."""
    global _pwm, _last_us
    if _pwm is not None:
        return
    from machine import Pin, PWM
    _last_us = None
    _pwm = PWM(Pin(3), freq=50, duty_u16=0)


def _require_started():
    if _pwm is None:
        raise RuntimeError('Call start() first')


def _command(us):
    global _last_us
    try:
        _pwm.duty_ns(us * 1000)
    except BaseException:
        stop()
        raise
    _last_us = us


def goto(us):
    """Explicit immediate position command; may cause a large physical movement."""
    _position(us)
    _require_started()
    _command(us)


def move(us, duration_ms=None):
    """Ramp from the last command while PWM remains active.

    With duration_ms, distribute steps over that nominal duration. Without it,
    use the configured directional step and interval. Timing is approximate.
    """
    _position(us)
    if duration_ms is not None:
        _integer(duration_ms, 'duration_ms', 1)
    _require_started()
    if _last_us is None:
        raise RuntimeError('Position unknown: explicitly call goto(us) first')
    origin = _last_us
    distance = abs(us - origin)
    if not distance:
        return
    direction = 1 if us > origin else -1
    prefix = 'TIGHTEN' if direction > 0 else 'RELEASE'
    step = _settings[prefix + '_STEP_US']
    count = (distance + step - 1) // step
    if duration_ms is not None and duration_ms < count:
        raise ValueError('duration_ms must allow at least 1 ms per step')
    previous_time = 0
    try:
        for index in range(1, count + 1):
            target_time = (index * duration_ms // count if duration_ms is not None
                           else index * _settings[prefix + '_INTERVAL_MS'])
            sleep_ms(target_time - previous_time)
            _command(origin + direction * min(index * step, distance))
            previous_time = target_time
    except BaseException:
        stop()
        raise


def configure(**changes):
    """Validate and update settings in RAM only; never move or write files."""
    global _settings
    candidate = dict(_settings)
    candidate.update(changes)
    _validate(candidate)
    _settings = candidate


def set_release(us):
    configure(RELEASE_US=us)


def set_engage(us):
    configure(ENGAGE_US=us)


def save():
    """Explicit temporary-file write and replacement; no delete-first fallback."""
    _validate(_settings)
    temporary = _CONFIG + '.tmp'
    with open(temporary, 'w') as stream:
        json.dump(_settings, stream)
        stream.write('\n')
        stream.flush()
    sync = getattr(os, 'sync', None)
    if sync is not None:
        sync()
    replace = getattr(os, 'replace', None)
    if replace is None:
        replace = os.rename
    # If this filesystem cannot replace an existing file, propagate the error
    # and preserve the original configuration rather than deleting it first.
    replace(temporary, _CONFIG)
    if sync is not None:
        sync()


def status():
    for key in _DEFAULTS:
        print(key + ' = ' + str(_settings[key]))
    print('PWM initialized:', _pwm is not None)
    print('Last commanded us:', _last_us)
    print('Physical position: not measured')
    print('Configuration file:', _CONFIG)


def stop():
    """Disable PWM and forget the commanded position, even if deinit fails."""
    global _pwm, _last_us
    pwm = _pwm
    _pwm = None
    _last_us = None
    if pwm is not None:
        pwm.deinit()
