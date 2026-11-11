"""MPR121 register driver extracted from the verified touch diagnostic.
Only bus access; no pins are initialized by import. Datasheet:
https://www.nxp.com/docs/en/data-sheet/MPR121.pdf
"""
from time import sleep_ms
ADDRESS = 0x5A
TOUCH_THRESHOLD = 12
RELEASE_THRESHOLD = 6

class MPR121:
    def __init__(self, bus):
        self.bus = bus

    def write(self, register, value):
        self.bus.writeto_mem(ADDRESS, register, bytes((value,)))

    def initialize(self):
        self.write(0x80, 0x63)  # Documented soft reset command.
        sleep_ms(10)
        self.write(0x5E, 0)  # Stop mode before configuration writes.
        if self.bus.readfrom_mem(ADDRESS, 0x5D, 1) != b'\x24':
            raise RuntimeError('MPR121 reset configuration check failed')
        # Rising/falling/touched baseline tracking filters, registers 0x2B–0x35.
        for register, value in enumerate((1, 1, 14, 0, 1, 5, 1, 0, 0, 0, 0), 0x2B):
            self.write(register, value)
        for electrode in (0, 1):
            self.write(0x41 + 2 * electrode, TOUCH_THRESHOLD)
            self.write(0x42 + 2 * electrode, RELEASE_THRESHOLD)
        self.write(0x5B, 0)     # Touch/release debounce: none.
        self.write(0x5C, 0x10)  # Global charge current 16 uA; FFI=6.
        self.write(0x5D, 0x20)  # Charge time 0.5 us; sample interval 1 ms.
        self.write(0x7B, 0)     # Automatic charge configuration disabled.
        self.write(0x5E, 0x82)  # Baseline initialization CL=10; ELE0/ELE1 only.
        if self.bus.readfrom_mem(ADDRESS, 0x5E, 1) != b'\x82':
            raise RuntimeError('MPR121 electrode enable check failed')
        sleep_ms(100)

    def sample(self):
        # Detect a reset/stopped sensor before accepting its touch bits.
        if self.bus.readfrom_mem(ADDRESS, 0x5E, 1) != b'\x82':
            raise OSError('MPR121 configuration lost or measurement stopped')
        # One contiguous read: touch/OOR status, filtered data and baselines.
        data = self.bus.readfrom_mem(ADDRESS, 0, 32)
        if len(data) != 32:
            raise OSError('Short MPR121 read')
        if data[0] & 0xFC or data[1] & 0x7F:
            raise OSError('Unexpected MPR121 touch-status bits')
        if data[1] & 0x80:
            raise OSError('MPR121 overcurrent flag')
        if data[2] & 3:
            raise OSError('MPR121 electrode out-of-range flag')
        filtered = (data[4] | ((data[5] & 3) << 8),
                    data[6] | ((data[7] & 3) << 8))
        baseline = (data[0x1E] << 2, data[0x1F] << 2)
        return (bool(data[0] & 1), bool(data[0] & 2)), filtered, baseline

    def stop(self):
        self.write(0x5E, 0)

