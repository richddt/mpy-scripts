import os
from machine import Pin, SPI, I2C, I2S
import asyncio
import fern
import canopy
import seesaw
import codec
import mixer
import math, time
from fps import FPS
from rotenc import RotaryEncoder
from tween import tween

MIRROR_KNOBS = False
MIRROR_PIPES = False
VERTICAL_FLIP = True

PatternRainbow = "CTP-eyJpZCI6IjE5NjEyMDE1LTFjMWEtNDk0Zi04YTFkLTA3YWI4NGUyM2MyYSIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjA5LFsxLDAsMF1dLFswLjIzLFsxLDEsMF1dLFswLjM4LFswLDEsMF1dLFswLjUsWzAsMSwxXV0sWzAuNjgsWzAsMCwxXV0sWzAuODMsWzEsMCwxXV0sWzEsWzEsMCwwXV1dfSwicGFyYW1zIjp7fSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOjAuNSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoicHJpbWFyeSIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InNhdyIsImlucHV0cyI6eyJ2YWx1ZSI6MC4zMywibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC42LCJyb3RhdGlvbiI6MH19XX0"
PatternProgress = "CTP-eyJpZCI6IjNhNzNiNjAxLWQ0ODctNDQzYS05YzFlLTlhNjg4NzY2MzIzMiIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicCI6W1swLFsxLDEsMV1dLFswLjg2LFsxLDEsMV1dLFsxLFswLDAsMF1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiY2hhc2VyIiwib3BhY2l0eSI6MSwiYmxlbmQiOiJtdWx0aXBseSIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6InByb2dyZXNzIiwic2l6ZSI6MX19XX0"
PatternRedYellowGreen = "CTP-eyJpZCI6ImNjMjc3NTc5LWZmMGUtNDJmNS1iOWViLWM1MGNjY2QxYTdjMCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMCwwXV0sWzAuMixbMSwwLDBdXSxbMC41MixbMSwwLjkyNTQ5MDE5NjA3ODQzMTQsMF1dLFsxLFswLDEsMC4wMTU2ODYyNzQ1MDk4MDM5Ml1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MX0sImxheWVycyI6W3siZWZmZWN0Ijoic29saWQiLCJvcGFjaXR5IjowLjcsImJsZW5kIjoibm9ybWFsIiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7Im9mZnNldCI6InByb2dyZXNzIn19XX0"


PatternRedGlow = "CTP-eyJpZCI6Ijg4ZWYzZDY3LWM3MzMtNDdhMS05NTFkLThiZDFlMDk5YzBiZiIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMC4wMSxbMCwwLDBdXSxbMC4wNyxbMSwwLDBdXSxbMC4yNyxbMC44MTE3NjQ3MDU4ODIzNTI5LDAuNjUwOTgwMzkyMTU2ODYyOCwwXV0sWzAuNTMsWzEsMCwwLjAzMTM3MjU0OTAxOTYwNzg0XV0sWzAuNzcsWzEsMC4zNDkwMTk2MDc4NDMxMzcyNCwwXV0sWzAuOTMsWzEsMCwwXV0sWzAuOTgsWzAsMCwwXV1dfSwicGFyYW1zIjp7InByb2dyZXNzIjowLjV9LCJsYXllcnMiOlt7ImVmZmVjdCI6ImdyYWRpZW50Iiwib3BhY2l0eSI6InByb2dyZXNzIiwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoicCIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InNhdyIsImlucHV0cyI6eyJ2YWx1ZSI6MC41NywibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC41LCJyb3RhdGlvbiI6MH19XX0"
PatternStaticRainbow = "CTP-eyJpZCI6Ijg4ZWYzZDY3LWM3MzMtNDdhMS05NTFkLThiZDFlMDk5YzBiZiIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjE1LFsxLDEsMF1dLFswLjMsWzAsMSwwXV0sWzAuNSxbMCwxLDFdXSxbMC43LFswLDAsMV1dLFswLjg1LFsxLDAsMV1dLFsxLFsxLDAsMF1dXSwiX2JsYWNrLXdoaXRlIjpbWzAsWzAsMCwwXV0sWzEsWzEsMSwxXV1dfSwicGFyYW1zIjp7InByb2dyZXNzIjoxfSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOiJwcm9ncmVzcyIsImJsZW5kIjoibm9ybWFsIiwicGFsZXR0ZSI6InByaW1hcnkiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuNTgsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fV19"
PatternPurple = "CTP-eyJpZCI6Ijg4ZWYzZDY3LWM3MzMtNDdhMS05NTFkLThiZDFlMDk5YzBiZiIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMCxbMSwwLDBdXSxbMC4yNyxbMC41MzcyNTQ5MDE5NjA3ODQzLDAsMC43MjE1Njg2Mjc0NTA5ODA0XV0sWzAuNSxbMCwwLDAuODcwNTg4MjM1Mjk0MTE3N11dLFswLjc3LFswLjM4NDMxMzcyNTQ5MDE5NjEsMCwwLjcyMTU2ODYyNzQ1MDk4MDRdXSxbMC45OSxbMC45NDExNzY0NzA1ODgyMzUzLDAsMF1dXSwiUGFsZXR0ZTIiOltbMCxbMSwwLjk4ODIzNTI5NDExNzY0NzEsMC45MDE5NjA3ODQzMTM3MjU1XV0sWzEsWzEsMC44OTQxMTc2NDcwNTg4MjM2LDAuMTgwMzkyMTU2ODYyNzQ1MV1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MX0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5IjoicHJvZ3Jlc3MiLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjU5LCJtaW4iOjAsIm1heCI6MX19LCJzaXplIjowLjUsInJvdGF0aW9uIjowfX1dfQ"
PatternPipeBlue = "CTP-eyJpZCI6Ijg4ZWYzZDY3LWM3MzMtNDdhMS05NTFkLThiZDFlMDk5YzBiZiIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAsMCwxXV0sWzAuMjgsWzAsMCwxXV0sWzAuNTcsWzEsMSwxXV0sWzAuODEsWzAsMC4xNjg2Mjc0NTA5ODAzOTIxNywxXV0sWzEsWzAsMCwxXV1dfSwicGFyYW1zIjp7InByb2dyZXNzIjowLjY2fSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOiJwcm9ncmVzcyIsImJsZW5kIjoibm9ybWFsIiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjUyLCJtaW4iOjAsIm1heCI6MX19LCJzaXplIjowLjI0LCJyb3RhdGlvbiI6MH19XX0"


PatternTest = "CTP-eyJpZCI6ImFhNDVjZDAyLThiYjAtNDc5Mi1iN2U3LTY5ZTFmZWNiNmViMSIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjE1LFsxLDEsMF1dLFswLjMsWzAsMSwwXV0sWzAuNSxbMCwxLDFdXSxbMC43LFswLDAsMV1dLFswLjg1LFsxLDAsMV1dLFsxLFsxLDAsMF1dXSwiX2JsYWNrLXdoaXRlIjpbWzAsWzAsMCwwXV0sWzEsWzEsMSwxXV1dfSwicGFyYW1zIjp7InByb2dyZXNzIjoxfSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJzb2xpZCIsIm9wYWNpdHkiOjEsImJsZW5kIjoibm9ybWFsIiwicGFsZXR0ZSI6InByaW1hcnkiLCJpbnB1dHMiOnsib2Zmc2V0IjoicHJvZ3Jlc3MifX1dfQ"


async def encoders_loop(encoders):
    for i, enc in enumerate(encoders):
        try:
            print("Starting encoder ", i + 1)
            await enc.start()
        except:
            print("Failed to start encoder ", i)

    while True:
        for i in range(4):
            await encoders[i].tick()
            await asyncio.sleep(0)


async def render_loop(encoders):
    canopy.init([fern.LED1_DATA, fern.LED2_DATA], 100)
    canopy.clear()
    canopy.render()

    # knobs are 24 LED rings, and we use the middle 18
    knob_segments = [canopy.Segment(0, 24 * i + 3, 18) for i in range(4)]

    # pipes are 16 LED strips and we use the middle 14. They are also
    # serpentine so flip every other strip
    pipe_segments = [
        canopy.Segment(
            1, 16 * i + 1, 14, not bool(i % 2) if VERTICAL_FLIP else bool(i % 2)
        )
        for i in range(4)
    ]

    if MIRROR_KNOBS:
        knob_segments = knob_segments[::-1]
    if MIRROR_PIPES:
        pipe_segments = pipe_segments[::-1]

    pattern_rainbow = canopy.Pattern(PatternRainbow)
    pattern_progress = canopy.Pattern(PatternProgress)
    pattern_knob = canopy.Pattern(PatternRedYellowGreen)
    pattern_pipe_red = canopy.Pattern(PatternRedGlow)
    pattern_pipe_rainbow = canopy.Pattern(PatternStaticRainbow)
    pattern_pipe_purple = canopy.Pattern(PatternPurple)
    pattern_pipe_blue = canopy.Pattern(PatternPipeBlue)

    pattern_test = canopy.Pattern(PatternTest)

    pipe_patterns = [
        pattern_pipe_red,
        pattern_pipe_purple,
        pattern_pipe_rainbow,
        pattern_pipe_blue,
    ]

    params = canopy.Params({"progress": 0.5})

    f = FPS(verbose=True)
    while True:
        f.tick()
        canopy.clear()
        for i in range(4):
            p = float(encoders[i].value)
            if p > 0.0:
                params["progress"] = p
                canopy.draw(pipe_segments[i], pipe_patterns[i], params)
                # canopy.draw(pipe_segments[i], pattern_rainbow)
                # canopy.draw(knob_segments[i], pattern_knob, params)
                canopy.draw(knob_segments[i], pipe_patterns[i])
                canopy.draw(knob_segments[i], pattern_progress, params)
        canopy.render()
        await asyncio.sleep(0)


async def main():
    # start i2c bus, encoders, audio
    i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA, freq=100000)
    encoders = [RotaryEncoder(i2c, addr, clicks=36) for addr in range(4)]

    asyncio.create_task(encoders_loop(encoders))
    asyncio.create_task(render_loop(encoders))

    asyncio.get_event_loop().run_forever()


asyncio.run(main())
