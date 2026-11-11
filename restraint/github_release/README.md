# Restraint

Restraint is an interactive installation using two capacitive handholds to
control a servo-driven rope mechanism. This repository contains the MPR121
production controller for a Chroma.tech Fern Rev D.

The installation has passed supervised integration tests, including full
10-second holds, automatic release, and mains power restoration during tightening
and holding. These tests do not constitute a safety certification.

## Hardware and wiring

- Chroma.tech Fern Rev D (ESP32-S3), running **MicroPython v1.26.0,
  Chroma.tech edition**.
- MPR121 capacitive touch sensor at I²C address **0x5A**.
- Two conductive handles connected to electrodes 0 and 1.
- DS5180SSG positional servo, separate suitable 5 V supply and common ground.
- Independent mechanical rope release.

Disconnect power before wiring. Use the tested power arrangement for the
installation; both Fern and servo supplies are switched off by its mains cutoff.

| Connection | Fern pin | ESP32-S3 GPIO / destination |
|---|---|---|
| Servo signal, 50 Hz PWM | D3 | GPIO3 |
| MPR121 SDA, 100 kHz SoftI2C | D6 | GPIO10 |
| MPR121 SCL | D7 | GPIO11 |
| MPR121 supply | 3.3 V | MPR121 VIN on the tested breakout |
| MPR121 ground | GND | MPR121 GND |
| Servo supply ground | GND | Common ground with separate servo supply |
| Handle 1 | — | MPR121 electrode 0 |
| Handle 2 | — | MPR121 electrode 1 |

GPIO1, GPIO2, GPIO9 and TouchPad are not used. Do not power the servo from the
Fern's 3.3 V rail.

## Installation

Use **mpremote v1.29.0** on the host. The board firmware must already be installed;
these instructions do not flash firmware. The files below belong in the Fern's
root filesystem.

Keep the mechanism unoccupied and servo power disconnected during installation.
For an existing installation, obtain an idle REPL first. `resume` avoids the
usual soft reset but mpremote can still interrupt running Python; do not use it
as a passive connection to an operating installation. Controller interruption
can perform cleanup and a deliberate hard reset. Allow recovery to finish before
continuing, and preserve any existing fault information.

Set `PORT` to the detected serial port and run these commands from this directory:

```sh
mpremote --version
mpremote connect list
PORT=/dev/cu.usbmodemYOUR_DEVICE

# Prevent automatic startup while installing.
mpremote connect "$PORT" resume exec "import os; f=open('/restraint_maintenance.flag','w'); f.write('Installation maintenance'); f.close(); os.sync()"

# Back up any existing main.py and configuration before replacing them.
# Omit these two reads only on a new board where the files do not exist.
mpremote connect "$PORT" resume fs cp :/main.py ./main.previous.py
mpremote connect "$PORT" resume fs cp :/servo_config.json ./servo_config.previous.json

mpremote connect "$PORT" resume fs cp restraint_main_mpr121.py :/restraint_main_mpr121.py
mpremote connect "$PORT" resume fs cp mpr121_sensor.py :/mpr121_sensor.py
mpremote connect "$PORT" resume fs cp servo_cal.py :/servo_cal.py
mpremote connect "$PORT" resume fs cp servo_config.json :/servo_config.json
mpremote connect "$PORT" resume fs cp restraint_diagnostic.py :/restraint_diagnostic.py
mpremote connect "$PORT" resume fs cp main.py :/main.py
```

Read each uploaded file back and compare it before activation. Do not overwrite
an existing installation's different calibration without separately reviewing
it. **Install `servo_config.json` alongside `servo_cal.py`: the module's legacy
missing-file defaults differ from this installation's tested values.**

Inspect `/restraint_run.lock` before activation. Never delete a genuine FAULT
merely to get the installation running. Once installation, calibration and an
unoccupied mechanism have been checked, explicitly remove maintenance protection:

```sh
mpremote connect "$PORT" resume exec "import os; os.remove('/restraint_maintenance.flag'); os.sync()"
```

This arms the next ordinary power-on; it does not start the controller immediately.
Disconnect the host and perform the supervised physical power-on. No `boot.py`
changes are required.

## Startup and interaction

`main.py` runs the MPR121 controller continuously, silently, without a retry loop.
An existing maintenance flag blocks startup before controller import. Ordinary
startup does not create that flag.

On a recognized power-on reset, provided no serious fault is latched:

1. Initialize PWM with no positioning pulses, then command **950 µs** as the first
   position. No previous position or engagement state is restored.
2. Initialize and validate the MPR121, then hold the release command for at least
   **2 seconds**, validating readings and feeding the watchdog every 20 ms.
3. Enter `WAIT_FOR_RELEASE`. Both electrodes must report released continuously
   for **200 ms** before entering `ARMED`.
4. Require a fresh both-touch interval of **100 ms** before `ENGAGING`.

The servo tightens quickly to 1600 µs, then more slowly to 2175 µs. When **2175 µs
is commanded**, the controller enters `HOLDING` and starts a **10,000 ms** timer.
This is a commanded endpoint, not an independently measured arrival.

If both touches remain valid through the hold, the controller emits the success
event exactly once and automatically releases:

```text
Restraint-Full Hold Succeeded
```

Production console output and optional recording are disabled by the launcher,
so the event is not printed to USB in this configuration. The controller retains
optional console/diagnostic support for supervised testing.

Loss of either touch during engagement or holding immediately requests release
on the next sensor sample, without contact-loss debounce. Release continues to
950 µs regardless of a renewed grip. After full commanded release, both handles
must be off for 200 ms, followed by a fresh 100 ms both-touch interval. Holding
the handles after automatic release never starts another engagement.

Sensor polling continues approximately every 20 ms throughout normal motion.
A separate **30,000 ms total-cycle safeguard** remains active. PWM stays enabled
during normal continuous operation, including the released state.

## Power recovery, faults and maintenance

An interrupted `RUNNING` marker alone does not prevent ordinary power-on recovery.
Every accepted startup follows the release-first sequence above. The unpowered
servo arm can move freely; startup may therefore cause a rapid initial movement.

The current firmware policy treats power-on and brownout reported as
`PWRON_RESET` alike. Other or unknown reset causes inhibit engagement. A brief
power disturbance is not guaranteed to be reported as power-on. A servo-only
power loss while the Fern stays powered is not detected by this logic.

I²C errors, invalid sensor readings and unexpected software exceptions inhibit
engagement and persist a FAULT. Cleanup attempts to command 950 µs while power is
available, settles, disables PWM and stops sensing. Watchdog resets and existing
serious faults block startup; ordinary power cycling never clears them. A frozen
controller cannot guarantee physical release. Flash failure or abrupt power loss
can prevent a new diagnostic/fault write from completing.

The ESP32 watchdog has no supported disable operation in this implementation.
Controlled shutdown and error cleanup end with a deliberate hard reset. The
controller does not automatically retry after a non-power reset.

To prevent startup for maintenance, with servo power disconnected and an idle
REPL, create `/restraint_maintenance.flag` using the installation command above.
This flag inhibits the launcher, not a controller already running. It also does
not block an explicit manual `run()` call. If the controller is running, use the
physical power cutoff or the established supervised Ctrl-C cleanup procedure;
do not assume disconnecting a host terminal stops it.

After diagnosing and correcting a genuine fault, explicit USB acknowledgement
is available through `restraint_main_mpr121.clear_fault(confirm=True)` while the
controller is stopped. It clears persistent records and acknowledges the current
reset cause, but does not initialize PWM or start the controller. Preserve fault
records before clearance. Do not automate this action.

## Calibration and files

`servo_config.json` is the authoritative installation configuration:

| Setting | Value |
|---|---:|
| RELEASE_US | 950 µs |
| ENGAGE_US | 2175 µs |
| ENGAGE_CROSSOVER_US | 1600 µs |
| FAST_TIGHTEN_STEP_US / FAST_TIGHTEN_INTERVAL_MS | 20 µs / 30 ms |
| TIGHTEN_STEP_US / TIGHTEN_INTERVAL_MS | 10 µs / 50 ms |
| RELEASE_STEP_US / RELEASE_INTERVAL_MS | 20 µs / 30 ms |
| MAX_ENGAGEMENT_MS (HOLDING duration) | 10000 ms |

Change calibration only with the controller stopped and the mechanism unloaded,
then review and test before restoring production. `servo_cal.py` provides explicit
`start`, `goto`, `move`, `set_release`, `set_engage`, `configure`, `save`, `status`
and `stop` commands. Importing it does not initialize hardware. Writes through
`save()` are explicit. Module limits of 700–2500 µs are not a promise of safe
mechanical travel for a particular installation.

The driver preserves tested MPR121 touch/release thresholds of 12/6. Startup
settling and the total-cycle safeguard are constants in the controller. Do not
change them as part of routine calibration.

`restraint_diagnostic.py` is retained for the controller's optional bounded
recording mode. It saves snapshots on boot and orderly/fault termination; RAM
events can be lost on sudden power removal. Generated snapshots, fault markers,
maintenance flags and logs are excluded from Git. They are not deployment files.

## Safety

This mechanism is **not safety-rated for restraining people**. It requires an
independent mechanical release and an appropriate electrical and mechanical
safety assessment. Keep people out of the rope mechanism during setup and tests,
and hands clear of moving hardware. Software commands do not verify position,
force, or physical release. Loss of electrical power cannot guarantee that a
loaded mechanism releases; the mechanical release must work independently.

## License

MIT; see [LICENSE](LICENSE).
