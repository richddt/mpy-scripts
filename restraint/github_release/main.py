"""Continuous MPR121 production launcher candidate; not installed automatically.

Normal power restoration never creates maintenance protection. Existing
maintenance and genuine fault protection remain authoritative. No retry loop.
"""
MAINTENANCE_FLAG = '/restraint_maintenance.flag'


def launch():
    import os
    controller = None
    try:
        try:
            os.stat(MAINTENANCE_FLAG)
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                raise
        else:
            return
        import restraint_main_mpr121 as controller
        # Checks persistent faults/reset cause before PWM; starts at RELEASE.
        # Continuous operation; diagnostics remain opt-in on manual run().
        controller.run(console=False, diagnostic=False)
    except BaseException as exc:
        if controller is not None and isinstance(exc, controller.StartupInhibited):
            return  # Preserve the original fault/reset diagnosis.
        # Only a launcher/software failure creates maintenance inhibition.
        # Never clear faults, retry, reset, or fall back to another controller.
        with open(MAINTENANCE_FLAG, 'w') as stream:
            stream.write('MPR121 launcher failure: ' + repr(exc)[:256] + '\n')
            stream.flush()
        os.sync()


if __name__ == '__main__':
    launch()
