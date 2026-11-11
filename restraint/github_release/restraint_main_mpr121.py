"""MPR121 continuous controller candidate; not a safety-rated restraint controller.

Import is inert. Explicit run() only; no boot integration. Before first use,
review and test independently with an unoccupied mechanism.

Recovery policy: PWRON_RESET is a recoverable fresh startup unless a
persistent FAULT exists. ESP32 MicroPython v1.26.0 reports power-on and
brownout identically; both intentionally use this same recovery policy.
An ordinary RUNNING/STOPPED marker does not turn a mains interruption into
a permanent fault. Watchdog, software and sensor fault records survive power
cycles. Unknown/non-power reset causes inhibit automatic engagement.
WDT remains active until explicit hard-reset shutdown after output cleanup.
No startup files are installed or modified by this module.

A watchdog/reset cannot guarantee physical release or eliminate servo force.
No physical position/force feedback is available. Mechanical release remains
independent of this software. Cleanup attempts release, then disables PWM.
"""

from time import ticks_ms, ticks_diff, sleep_ms

POLL_MS = 20
WATCHDOG_MS = 5000
HEALTH_LIMIT_MS = 100
RUN_LATCH = '/restraint_run.lock'
_running = False
_state = 'STOPPED'
_reset_acknowledged = False
_startup_consumed = False
RELEASE_SETTLE_MS = 1500
STARTUP_SETTLE_MS = 2000
# Independent fault deadline from engagement start through commanded release.
# Normal motion (~4 s), hold (10 s), and release (~2 s) fit within this bound.
MAX_CYCLE_MS = 30000


_log_start = None
_diagnostic = None
_console_enabled = False

def log(*args):
    elapsed = ticks_diff(ticks_ms(), _log_start) if _log_start is not None else 0
    if _diagnostic is not None:
        _diagnostic.event(elapsed, args)
    if not _console_enabled:
        return
    began = ticks_ms()
    try:
        print('[%6d ms]' % elapsed, *args)
    finally:
        if _diagnostic is not None:
            _diagnostic.print_duration(elapsed, ticks_diff(ticks_ms(), began))


def classify(touch):
    if (not isinstance(touch, (tuple, list)) or len(touch) != 2 or
            any(type(value) is not bool for value in touch)):
        raise ValueError('Invalid MPR121 touch status')
    return 'CONNECTED' if touch[0] and touch[1] else 'RELEASED'


class Controller:
    """One bounded servo step per update; no sleeps or blocking sweeps."""

    def __init__(self, settings, command, now, log=log):
        self.settings = settings
        self.command = command
        self.log = log
        self.release = settings['RELEASE_US']
        self.engage = settings['ENGAGE_US']
        self.crossover = settings['ENGAGE_CROSSOVER_US']
        self.slow_logged = False
        self.position = self.release  # run() explicitly commanded this first.
        self.target = self.release
        self.last_step = now
        self.classification = None
        self.released_since = None
        self.connected_since = None
        self.engaging_since = None
        self.holding_since = None
        self.cycle_since = None
        self.stop_requested = False
        self.last_touch_at = None
        self.last_touch = None
        self.summary_since = now
        self.state = 'WAIT_FOR_RELEASE'
        self.log('State:', self.state)

    def _transition(self, state, now):
        self.state = state
        if state == 'ENGAGING':
            self.slow_logged = False
            self.engaging_since = now
            self.cycle_since = now
        else:
            self.engaging_since = None
        self.holding_since = now if state == 'HOLDING' else None
        if state == 'WAIT_FOR_RELEASE':
            self.cycle_since = None
        self.connected_since = None
        self.released_since = None
        self.log('State:', state)
        if state == 'HOLDING':
            self.log('Hold timer started:', self.settings['MAX_ENGAGEMENT_MS'],
                     'ms; engaged endpoint commanded, physical arrival not measured')

    def request_stop(self, now):
        """Latch a cooperative stop; no future input can initiate engagement."""
        if self.stop_requested:
            return
        self.stop_requested = True
        self.target = self.release
        if self.position != self.release:
            if self.state != 'RELEASING':
                self.last_step = None
                self._transition('RELEASING', now)
        else:
            self._transition('WAIT_FOR_RELEASE', now)

    def update(self, touch, now):
        try:
            state = classify(touch)
        except ValueError:
            self.request_stop(now)
            raise
        self.last_touch_at = now
        self.last_touch = tuple(touch)
        if state != self.classification:
            self.log('Touch classification:', state, 'E0/E1:', touch)
            self.classification = state

        if self.stop_requested:
            self.advance(now)
            return

        if self.state == 'WAIT_FOR_RELEASE':
            # Start qualifying only after the release endpoint was commanded.
            # Either-hand loss releases motion, but BOTH hands must be off
            # continuously before a fresh grip may arm another cycle.
            if not touch[0] and not touch[1]:
                if self.released_since is None:
                    self.released_since = now
                if ticks_diff(now, self.released_since) >= 200:
                    self._transition('ARMED', now)
            else:
                self.released_since = None
            return

        if self.state == 'ARMED':
            if state == 'CONNECTED':
                if self.connected_since is None:
                    self.connected_since = now
                if ticks_diff(now, self.connected_since) >= 100:
                    self.target = self.engage
                    self.last_step = None
                    self._transition('ENGAGING', now)
            else:
                self.connected_since = None
            if self.state == 'ARMED':
                return

        if self.state in ('ENGAGING', 'HOLDING') and state != 'CONNECTED':
            if _diagnostic is not None:
                elapsed = ticks_diff(now, _log_start) if _log_start is not None else 0
                _diagnostic.event(elapsed, ('Release reason: contact loss', state, touch))
            self.target = self.release
            self.last_step = None
            self._transition('RELEASING', now)

        self.advance(now)

    def diagnostic_summary(self, now):
        """One bounded summary per second; no sample history or catch-up loop."""
        if ticks_diff(now, self.summary_since) < 1000:
            return
        released = (min(200, ticks_diff(now, self.released_since))
                    if self.released_since is not None else 0)
        connected = (min(100, ticks_diff(now, self.connected_since))
                     if self.connected_since is not None else 0)
        engaged = (ticks_diff(now, self.engaging_since)
                   if self.engaging_since is not None else None)
        self.log('Status:', self.state, 'E0/E1:', self.last_touch,
                 'classification:', self.classification,
                 'release_ms:', released, '/200',
                 'connected_ms:', connected, '/100',
                 'engagement_ms:', engaged,
                 'holding_ms:', (ticks_diff(now, self.holding_since)
                                if self.holding_since is not None else None),
                 'cycle_ms:', (ticks_diff(now, self.cycle_since)
                              if self.cycle_since is not None else None))
        self.summary_since = now

    def advance(self, now):
        """Service motion between sensor polls, preserving 30/50 ms intervals."""
        if (self.cycle_since is not None and
                ticks_diff(now, self.cycle_since) >= MAX_CYCLE_MS):
            self.request_stop(now)
            self.log('FAULT: maximum total cycle duration reached:', MAX_CYCLE_MS)
            # Existing run() exception handling persists FAULT and attempts
            # release, settling, PWM disable and watchdog-reset cleanup.
            raise RuntimeError('Maximum total cycle duration exceeded')
        # Only the commanded endpoint starts the hold. Contact changes are
        # processed before this check; no successful hold on contact loss.
        if (self.state == 'HOLDING' and
                ticks_diff(now, self.holding_since) >= self.settings['MAX_ENGAGEMENT_MS']):
            self.log('Maximum hold duration reached:',
                     self.settings['MAX_ENGAGEMENT_MS'], 'ms; forcing release')
            # Require a successful, current MPR121 read at the deadline. A failed
            # read or shutdown must never announce a successful hold.
            if (not self.stop_requested and self.classification == 'CONNECTED'
                    and self.last_touch_at == now):
                if _console_enabled:
                    print('Restraint-Full Hold Succeeded')
                elif _diagnostic is not None:
                    _diagnostic.event(ticks_diff(ticks_ms(), _log_start),
                                      ('Restraint-Full Hold Succeeded',))
            self.target = self.release
            self.last_step = None
            self._transition('RELEASING', now)
        # RELEASING is latched: CONNECTED is logged but cannot change target.
        if self.position == self.target:
            return
        tightening = self.target > self.position
        fast = tightening and self.position < self.crossover
        prefix = ('FAST_TIGHTEN' if fast else 'TIGHTEN') if tightening else 'RELEASE'
        interval = self.settings[prefix + '_INTERVAL_MS']
        if self.last_step is not None and ticks_diff(now, self.last_step) < interval:
            return
        step = self.settings[prefix + '_STEP_US']
        candidate = (min(self.position + step, self.target) if tightening
                     else max(self.position - step, self.target))
        if fast:
            candidate = min(candidate, self.crossover)
        candidate = max(self.release, min(self.engage, candidate))
        self.command(candidate)
        self.position = candidate
        self.last_step = now
        if tightening and self.position >= self.crossover and not self.slow_logged:
            self.log('Slow engagement zone entered:', self.position)
            self.slow_logged = True
        if self.position == self.target:
            self.log('Endpoint commanded:', self.position, '(physical position not measured)')
            if self.state == 'ENGAGING':
                self._transition('HOLDING', now)
            elif self.state == 'RELEASING':
                self._transition('WAIT_FOR_RELEASE', now)



def _read_latch():
    try:
        with open(RUN_LATCH, 'r') as stream:
            return stream.read()
    except OSError as exc:
        if exc.args and exc.args[0] == 2:
            return None
        raise


def _write_latch(message):
    import os
    # Existing marker still blocks startup if writing/replacement is interrupted.
    temporary = RUN_LATCH + '.tmp'
    with open(temporary, 'w') as stream:
        stream.write(message + '\n')
        stream.flush()
    os.sync()
    os.rename(temporary, RUN_LATCH)
    os.sync()


class StartupInhibited(RuntimeError):
    """Startup policy refusal, not a new runtime fault."""


def _check_startup():
    global _state
    from machine import reset_cause, WDT_RESET, PWRON_RESET
    cause = reset_cause()
    marker = _read_latch()
    log('Reset cause:', cause, 'persistent latch:', repr(marker))
    # Never overwrite original fault diagnostics with a later boot refusal.
    if marker is not None and not marker.startswith(('RUNNING:', 'STOPPED:')):
        _state = 'FAULT'
        raise StartupInhibited('FAULT: persistent fault or corrupt marker; explicit clearance required')
    if _state == 'FAULT':
        raise StartupInhibited('FAULT: explicit operator clearance required')
    if _startup_consumed:
        _state = 'INHIBITED'
        raise StartupInhibited('Restart inhibited within this interpreter; explicit clearance required')
    if _reset_acknowledged:
        # Clearance removes markers and acknowledges this boot only.
        if marker is not None:
            _state = 'INHIBITED'
            raise StartupInhibited('Run marker present after acknowledgement; inspect before retry')
        return
    if cause == WDT_RESET:
        _state = 'FAULT'
        _write_latch('FAULT: watchdog reset; machine cause=%s' % cause)
        raise StartupInhibited('FAULT: watchdog reset; explicit clearance required')
    if cause == PWRON_RESET:
        _state = 'STOPPED'
        log('Power-on/brownout recovery: fresh release/arming sequence required')
        return
    # HARD_RESET may represent panic; SOFT_RESET, deep sleep and unknown
    # causes also do not authorize automatic recovery. Preserve existing data.
    _state = 'INHIBITED'
    raise StartupInhibited('Non-power/unknown reset: no PWM; operator clearance required')


def clear_fault(confirm=False):
    """USB operator acknowledgement only; no pins, PWM, WDT or run() calls."""
    global _state, _reset_acknowledged, _startup_consumed
    if confirm is not True or _running:
        raise RuntimeError('Inspect mechanism first; controller must be stopped')
    import os
    # Remove an interrupted temporary write before removing the blocking marker.
    for path in (RUN_LATCH + '.tmp', RUN_LATCH):
        try:
            os.remove(path)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
    os.sync()
    _startup_consumed = False
    _reset_acknowledged = True  # Acknowledge sticky reset cause for this interpreter.
    _state = 'STOPPED'
    log('Fault cleared by operator; controller remains stopped')


def clear_run_latch(confirm=False):
    """Compatibility alias for the explicit operator recovery command."""
    clear_fault(confirm)


def status():
    from machine import reset_cause
    print('Controller state:', _state)
    print('Running:', _running)
    print('Reset cause:', reset_cause())
    print('Persistent latch:', repr(_read_latch()))


def _claim_run():
    global _startup_consumed
    _check_startup()
    _write_latch('RUNNING: ordinary interrupted run; not a diagnosed fault')
    _startup_consumed = True


def run(test_duration_ms=None, diagnostic=False, console=False):
    """Explicit start; power-on/brownout recovers through fresh release/arming.
    test_duration_ms=None is continuous; a positive duration requests release
    at the deadline, settles, disables outputs, and deliberately hard-resets.
    Console and diagnostic recording are opt-in (both default False).
    No previous position, engagement or timer is resumed after any reset.
    """
    global _running, _log_start, _state, _diagnostic, _console_enabled
    if test_duration_ms is not None:
        if type(test_duration_ms) is not int or not 1 <= test_duration_ms <= 3600000:
            raise ValueError('test_duration_ms must be None or 1..3600000')
    if _running:
        raise RuntimeError('Controller already running')
    _console_enabled = console
    from machine import Pin, SoftI2C, WDT, reset
    sensor = None
    controller = None
    servo = None
    started = False
    failure = None
    watchdog = None
    test_settled = False
    _running = True
    _log_start = ticks_ms()
    try:
        if diagnostic:
            from restraint_diagnostic import Recorder
            from machine import reset_cause
            _diagnostic = Recorder()
            # Only before PWM/WDT initialization: no flash writes in polling.
            _diagnostic.boot(reset_cause(), _read_latch())
        _claim_run()
        import servo_cal as servo
        if servo._pwm is not None:
            raise RuntimeError('Existing PWM is active; inspect before starting')
        settings = servo._load()
        servo.configure(**settings)
        log('Continuous controller; saved calibration:', settings)
        watchdog = WDT(timeout=WATCHDOG_MS)
        _state = 'RUNNING'
        servo.start()
        started = True
        servo.goto(settings['RELEASE_US'])
        log('Startup RELEASE commanded:', settings['RELEASE_US'])
        from mpr121_sensor import MPR121
        sensor = MPR121(SoftI2C(sda=Pin(10), scl=Pin(11), freq=100000))
        sensor.initialize()
        # PWM continuously emits RELEASE pulses. Validate sensing during settling,
        # but discard all touch history until a fresh Controller is constructed.
        startup_settle = ticks_ms()
        log('Startup release settling:', STARTUP_SETTLE_MS, 'ms; engagement inhibited')
        while ticks_diff(ticks_ms(), startup_settle) < STARTUP_SETTLE_MS:
            sample_began = ticks_ms()
            touch, filtered, baseline = sensor.sample()
            classify(touch)
            if ticks_diff(ticks_ms(), sample_began) > HEALTH_LIMIT_MS:
                raise RuntimeError('Software watchdog: startup MPR121 read stalled')
            servo.goto(settings['RELEASE_US'])
            watchdog.feed()
            sleep_ms(POLL_MS)
            if ticks_diff(ticks_ms(), sample_began) > HEALTH_LIMIT_MS:
                raise RuntimeError('Software watchdog: startup settling stalled')
        log('Startup release settling complete; fresh release qualification required')
        controller = Controller(settings, servo.goto, ticks_ms())
        last_poll = None
        last_sample = None
        previous_pass = ticks_ms()
        test_began = previous_pass
        settle_since = None
        if test_duration_ms is not None:
            log('Controlled test duration:', test_duration_ms, 'ms from initialization complete')
        def check_deadline(now):
            if (test_duration_ms is not None and not controller.stop_requested and
                    ticks_diff(now, test_began) >= test_duration_ms):
                log('Test deadline reached; engagement disabled; completing release')
                controller.request_stop(now)
        while True:
            now = ticks_ms()
            if ticks_diff(now, previous_pass) > HEALTH_LIMIT_MS:
                raise RuntimeError('Software watchdog: loop stalled')
            previous_pass = now
            check_deadline(now)
            hold_due = (controller.state == 'HOLDING' and
                        ticks_diff(now, controller.holding_since) >=
                        settings['MAX_ENGAGEMENT_MS'])
            if last_poll is None or ticks_diff(now, last_poll) >= POLL_MS or hold_due:
                last_poll = now
                try:
                    touch, filtered, baseline = sensor.sample()
                    classify(touch)  # Validate before any engagement decision.
                    if ticks_diff(ticks_ms(), now) > HEALTH_LIMIT_MS:
                        raise RuntimeError('Software watchdog: MPR121 read stalled')
                except Exception:
                    controller.request_stop(ticks_ms())
                    raise  # Persistent fault + existing release/PWM cleanup.
                last_sample = ticks_ms()
                check_deadline(last_sample)
                controller.update(touch, last_sample)
            else:
                controller.advance(now)
            controller.diagnostic_summary(ticks_ms())
            if (last_sample is None or
                    ticks_diff(ticks_ms(), last_sample) > HEALTH_LIMIT_MS or
                    ticks_diff(ticks_ms(), now) > HEALTH_LIMIT_MS):
                raise RuntimeError('Software watchdog: stale MPR121 sample or stalled control pass')
            watchdog.feed()
            if controller.stop_requested and controller.position == controller.release:
                if settle_since is None:
                    settle_since = ticks_ms()
                    log('Test release endpoint commanded; settling')
                if ticks_diff(ticks_ms(), settle_since) >= RELEASE_SETTLE_MS:
                    test_settled = True
                    log('Controlled test release settling complete')
                    break
            sleep_ms(1)
    except StartupInhibited as exc:
        failure = exc
        log('Startup inhibited; PWM not enabled:', str(exc))
    except BaseException as exc:
        failure = exc
        _state = 'STOPPED' if isinstance(exc, KeyboardInterrupt) else 'FAULT'
        log('State:', _state, 'engagement inhibited:', repr(exc))
        try:
            marker = _read_latch()
            if marker is None or not marker.startswith('FAULT:'):
                _write_latch(_state + ': ' + repr(exc))
        except BaseException as latch_error:
            _state = 'FAULT'
            log('ERROR persisting fault; pre-run latch remains the fallback:', repr(latch_error))
    finally:
        # No more sensor updates or engagement decisions once cleanup begins.
        if started and not test_settled:
            try:
                log('Shutdown/error: commanding RELEASE:', settings['RELEASE_US'])
                servo.goto(settings['RELEASE_US'])
                settle = ticks_ms()
                while ticks_diff(ticks_ms(), settle) < RELEASE_SETTLE_MS:
                    sleep_ms(10)
                log('Release settling complete (physical arrival not measured)')
            except BaseException as exc:
                _state = 'FAULT'
                log('ERROR requesting release:', repr(exc))
                if failure is None:
                    failure = exc
        if servo is not None:
            try:
                servo.stop()
                log('PWM disabled')
            except BaseException as exc:
                _state = 'FAULT'
                log('ERROR disabling PWM:', repr(exc))
                if failure is None:
                    failure = exc
        if sensor is not None:
            try:
                sensor.stop()
                log('MPR121 measurement disabled')
            except BaseException as exc:
                _state = 'FAULT'
                log('ERROR stopping MPR121:', repr(exc))
                if failure is None:
                    failure = exc
        _running = False
        if failure is not None and not isinstance(failure, (KeyboardInterrupt, StartupInhibited)):
            _state = 'FAULT'
        if _state == 'FAULT' and not isinstance(failure, StartupInhibited):
            try:
                marker = _read_latch()
                if marker is None or not marker.startswith('FAULT:'):
                    _write_latch('FAULT: shutdown or controller error; inspect logs')
            except BaseException as exc:
                log('ERROR persisting cleanup fault:', repr(exc))
        if test_settled and failure is None and _state != 'FAULT':
            try:
                # Write completion only after PWM disable succeeded; never
                # remove/overwrite genuine fault diagnostics automatically.
                marker = _read_latch()
                if marker is not None and marker.startswith('FAULT:'):
                    raise RuntimeError('Persistent fault detected at test completion')
                _write_latch('STOPPED: controlled test completed; outputs disabled')
                _state = 'STOPPED'
                log('Controlled test complete; PWM disabled; MPR121 stopped; no fault')
                watchdog.feed()
            except BaseException as exc:
                _state = 'FAULT'
                failure = exc
                log('ERROR finalizing controlled test:', repr(exc))
                try:
                    if not (_read_latch() or '').startswith('FAULT:'):
                        _write_latch('FAULT: test completion error: ' + repr(exc))
                except BaseException as latch_error:
                    log('ERROR persisting completion fault:', repr(latch_error))
        if _diagnostic is not None:
            try:
                _diagnostic.finish(_state, repr(failure), _read_latch())
            except Exception as exc:
                # No USB output, even when the diagnostic storage fails.
                # Retain an explicit error in the existing fault marker.
                if not (_read_latch() or '').startswith('FAULT:'):
                    _write_latch('FAULT: diagnostic save failed: ' + repr(exc))
            finally:
                _diagnostic = None
        if watchdog is not None:
            # WDT has no supported deinit. End the session with a deliberate
            # hard reset after cleanup instead of waiting for accidental expiry.
            log('Outputs cleanup attempted; latch retained; explicit hard reset now')
            reset()
            # Real machine.reset() does not return. If it fails to reset, refuse
            # to feed WDT; its eventual reset still leaves the startup latch.
            raise RuntimeError('machine.reset unexpectedly returned; restart prohibited')
    if failure is not None:
        raise failure


# No __main__ call or automatic startup. Operator must explicitly invoke run().
