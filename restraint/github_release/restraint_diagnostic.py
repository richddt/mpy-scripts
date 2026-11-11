"""Opt-in bounded recorder; importing performs no I/O or hardware access.

No flash writes during polling. A hard reset/power loss can lose RAM events.
Existing fault latch remains the authoritative fault record.
"""
import json
import os

LIMIT = 128
TEXT_LIMIT = 192
BOOT_PATH = '/restraint_diag_boot.json'
RUN_PATH = '/restraint_diag_run.json'


def write_snapshot(path, data):
    with open(path + '.tmp', 'w') as stream:
        json.dump(data, stream)
        stream.flush()
    os.sync()
    os.rename(path + '.tmp', path)
    os.sync()


class Recorder:
    def __init__(self):
        self.records = []
        self.dropped = 0
        self.max_print_ms = 0
        self.cause = None

    def boot(self, cause, latch):
        self.cause = cause
        write_snapshot(BOOT_PATH, {'reset_cause': cause,
                                  'prior_latch': str(latch)[:TEXT_LIMIT]})

    def event(self, elapsed, args):
        # Keep a fixed number of recent events; never retain a raw sample stream.
        text = ' '.join(str(arg) for arg in args)[:TEXT_LIMIT]
        if len(self.records) == LIMIT:
            self.records.pop(0)
            self.dropped += 1
        self.records.append((elapsed, text))

    def print_duration(self, elapsed, duration):
        self.max_print_ms = max(self.max_print_ms, duration)
        if duration >= 20:
            self.event(elapsed, ('Slow console write ms:', duration))

    def finish(self, state, failure, latch):
        write_snapshot(RUN_PATH, {
            'reset_cause': self.cause, 'state': state,
            'failure': failure[:TEXT_LIMIT], 'latch': str(latch)[:TEXT_LIMIT],
            'max_print_ms': self.max_print_ms, 'dropped': self.dropped,
            'events': self.records,
        })
