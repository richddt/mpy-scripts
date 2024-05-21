from machine import Pin, SPI, I2C, I2S
import asyncio
import fern
import nfc
import seesaw
import canopy
from tween import tween
from fps import FPS
from rotenc import RotaryEncoder

PatternRedYellowGreen = "CTP-eyJpZCI6IjMzNzIzOGZjLTIyMTEtNDlhZS04MTQwLWFmMDIyNDAxMGZlOCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMCwwXV0sWzAuMixbMSwwLDBdXSxbMC41MixbMSwwLjkyNTQ5MDE5NjA3ODQzMTQsMF1dLFsxLFswLDEsMC4wMTU2ODYyNzQ1MDk4MDM5Ml1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MC42OH0sImxheWVycyI6W3siZWZmZWN0Ijoic29saWQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJQYWxldHRlMSIsImlucHV0cyI6eyJvZmZzZXQiOiJwcm9ncmVzcyJ9fV19"
PatternProgress = "CTP-eyJpZCI6IjNhNzNiNjAxLWQ0ODctNDQzYS05YzFlLTlhNjg4NzY2MzIzMiIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicCI6W1swLFsxLDEsMV1dLFswLjg2LFsxLDEsMV1dLFsxLFswLDAsMF1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiY2hhc2VyIiwib3BhY2l0eSI6MSwiYmxlbmQiOiJtdWx0aXBseSIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6InByb2dyZXNzIiwic2l6ZSI6MX19XX0"


async def render_loop(encoders):
    segments = [
        canopy.Segment(0, 3, 18),
        canopy.Segment(0, 27, 18),
        canopy.Segment(0, 51, 18),
        canopy.Segment(0, 75, 18),
    ]

    s = canopy.Segment(0, 0, 100)

    pattern_bg = canopy.Pattern(PatternRedYellowGreen)
    pattern_fg = canopy.Pattern(PatternProgress)

    f = FPS(verbose=True)
    p = canopy.Params({"progress": 0.5})

    while True:
        f.tick()
        canopy.clear()
        for i in range(4):
            p["progress"] = encoders[i].value
            canopy.draw(segments[i], pattern_bg, p)
            canopy.draw(segments[i], pattern_fg, p)
        canopy.render()
        await asyncio.sleep(0)


async def encoders_loop(encoders):
    print("Starting encoders loop")
    while True:
        for i in range(4):
            await encoders[i].tick()
            await asyncio.sleep(0)


async def main():

    i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA, freq=100000)
    print(i2c.scan())

    canopy.init([fern.LED1_DATA, fern.LED2_DATA], 100)
    canopy.clear()
    canopy.render()

    encoders = [RotaryEncoder(i2c, addr, clicks=36) for addr in range(4)]

    for i, enc in enumerate(encoders):
        try:
            print("Starting encoder ", i)
            await enc.start()
        except:
            print("Failed to start encoder ", i)
            raise

    asyncio.create_task(render_loop(encoders))
    asyncio.create_task(encoders_loop(encoders))
    asyncio.get_event_loop().run_forever()


asyncio.run(main())
