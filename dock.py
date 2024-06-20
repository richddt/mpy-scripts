from machine import SPI, I2C, Pin, I2S
import sys
import fern
import codec
import json
import canopy
import nfc
import asyncio
from fps import FPS
from tween import tween
import mixer

PatternRainbow = "CTP-eyJpZCI6IjE5NjEyMDE1LTFjMWEtNDk0Zi04YTFkLTA3YWI4NGUyM2MyYSIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjA5LFsxLDAsMF1dLFswLjIzLFsxLDEsMF1dLFswLjM4LFswLDEsMF1dLFswLjUsWzAsMSwxXV0sWzAuNjgsWzAsMCwxXV0sWzAuODMsWzEsMCwxXV0sWzEsWzEsMCwwXV1dfSwicGFyYW1zIjp7fSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOjAuNSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoicHJpbWFyeSIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InNhdyIsImlucHV0cyI6eyJ2YWx1ZSI6MC4zMywibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC42LCJyb3RhdGlvbiI6MH19XX0"
PatternBlue = "CTP-eyJpZCI6IjNmNDdmYjAwLWFlYTgtNDEwYy1hMzk2LTEwYmY3Yjc0NDA2MyIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAsMC4xMzMzMzMzMzMzMzMzMzMzMywxXV0sWzAuNSxbMCwwLjE2ODYyNzQ1MDk4MDM5MjE3LDFdXSxbMSxbMCwwLDFdXV19LCJwYXJhbXMiOnsiaW11LnNoYWtlIjowfSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOnsidHlwZSI6InNpbiIsImlucHV0cyI6eyJ2YWx1ZSI6MC41NywibWluIjowLjMyLCJtYXgiOjF9fSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuMjcsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNTQsInJvdGF0aW9uIjowfX0seyJlZmZlY3QiOiJzcGFya2xlcyIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im11bHRpcGx5IiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuMTMsIm9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX1dfQ"
PatternRed = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMC4wMSxbMCwwLDBdXSxbMC4wNyxbMSwwLDBdXSxbMC4yNyxbMC44MTE3NjQ3MDU4ODIzNTI5LDAuNjUwOTgwMzkyMTU2ODYyOCwwXV0sWzAuNTMsWzEsMCwwLjAzMTM3MjU0OTAxOTYwNzg0XV0sWzAuNzcsWzEsMC4zNDkwMTk2MDc4NDMxMzcyNCwwXV0sWzAuOTMsWzEsMCwwXV0sWzAuOTgsWzAsMCwwXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0Ijoic3BhcmtsZXMiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuODUsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX0seyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MC4wOCwibWF4IjowLjQ0fX0sInNpemUiOjAuNzUsInJvdGF0aW9uIjowfX1dfQ"
PatternPurple = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMCxbMSwwLDBdXSxbMC4zMSxbMC42MDc4NDMxMzcyNTQ5MDE5LDAsMC44MTE3NjQ3MDU4ODIzNTI5XV0sWzAuNSxbMCwwLDAuODkwMTk2MDc4NDMxMzcyNV1dLFswLjc2LFswLjUzMzMzMzMzMzMzMzMzMzMsMCwxXV0sWzAuOTgsWzEsMCwwXV1dLCJQYWxldHRlMiI6W1swLFsxLDAuOTg4MjM1Mjk0MTE3NjQ3MSwwLjkwMTk2MDc4NDMxMzcyNTVdXSxbMSxbMSwwLjg5NDExNzY0NzA1ODgyMzYsMC4xODAzOTIxNTY4NjI3NDUxXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fSx7ImVmZmVjdCI6InNwYXJrbGVzIiwib3BhY2l0eSI6ImltdS5zaGFrZSIsImJsZW5kIjoibm9ybWFsLW5vbmJsYWNrIiwicGFsZXR0ZSI6IlBhbGV0dGUyIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuNTEsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX19fV19"

PatternIdle = "CTP-eyJpZCI6IjcyZTczYjJkLWFjMjEtNDk4ZC04OGQyLTA1MTk5NDllZDZiNiIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMC44Mjc0NTA5ODAzOTIxNTY4LDAuNl1dXX0sInBhcmFtcyI6e30sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5Ijp7InR5cGUiOiJzaW4iLCJpbnB1dHMiOnsidmFsdWUiOjAuNCwibWluIjowLjA2LCJtYXgiOjAuNDJ9fSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuMjcsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNTQsInJvdGF0aW9uIjowfX1dfQ"


alpha = tween()

m = mixer.Mixer()
sounds = {}

Mode = namedtuple("Mode", ["name", "pattern"])
modes = [
    Mode("rainbow", PatternRainbow),
    Mode("blue", PatternBlue),
    Mode("red", PatternRed),
    Mode("purple", PatternPurple),
]
current_mode = "rainbow"
pattern_idle = canopy.Pattern(PatternIdle)
pattern_active = canopy.Pattern(PatternIdle)


def set_mode(mode):
    global current_mode
    global pattern_active
    for m in modes:
        if m.name == mode:
            print("Setting mode to ", mode)
            current_mode = mode
            pattern_active = canopy.Pattern(m.pattern)


async def tag_found(reader):
    try:
        # print("Tag found ", reader.tag)
        print(json.dumps({"cmd": "tag_found", "id": reader.tag.uid.hex()}))
        m.play(sounds["dock"])
        alpha.tween(1, 0.3)

        try:
            tag = await reader.readNdef()
        except Exception as e:
            print("Error reading tag: ", e)

        while True:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        alpha.tween(0, 0.6)
        # print("Tag lost")
        m.play(sounds["undock"])
        print(json.dumps({"cmd": "tag_lost"}))


async def render_loop():
    seg = canopy.Segment(0, 0, 40)
    pattern = canopy.Pattern(PatternRainbow)
    alpha.tween(0, 0)
    f = FPS(verbose=False)
    while True:
        f.tick()
        canopy.clear()
        canopy.draw(seg, pattern)
        canopy.brightness(alpha.value)
        canopy.render()
        await asyncio.sleep(0.001)


async def input_loop():
    sreader = asyncio.StreamReader(sys.stdin)
    while True:
        line = sreader.readline()
        try:
            cmd = json.loads(line)
            if cmd["cmd"] == "color":
                c = cmd["value"]
                # render this color to DMX output channel
                # TODO
        except:
            print("Invalid JSON cmd: ", line)
            continue


async def play_audio_loop(audio_out):
    swriter = asyncio.StreamWriter(audio_out)
    wav_samples = bytearray(5000)
    wav_samples_mv = memoryview(wav_samples)

    while True:
        m.mixinto(wav_samples_mv)
        swriter.out_buf = wav_samples_mv[:]
        await swriter.drain()


async def main():
    # open I2S first!! we get weird static sounds if we don't
    audio_out = I2S(
        0,
        sck=Pin(fern.I2S_BCK),
        ws=Pin(fern.I2S_WS),
        sd=Pin(fern.I2S_SDOUT),
        mck=Pin(fern.I2S_MCK),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=16000,
        ibuf=10000,
    )

    # print("Mounting SD card")
    # fern.mount_sdcard()

    sounds["dock"] = mixer.Voice("/orbdock.wav")
    sounds["undock"] = mixer.Voice("/orbundock.wav")

    print("Opening NFC reader")
    spi = SPI(
        1, baudrate=7000000, sck=fern.NFC_SCK, mosi=fern.NFC_MOSI, miso=fern.NFC_MISO
    )
    reader = nfc.NfcReader(spi, fern.NFC_NSS, fern.NFC_BUSY, fern.NFC_RST)
    reader.onTagFound(tag_found)
    try:
        await reader.start(verbose=False)
        asyncio.create_task(reader.loop())
    except Exception as e:
        print("No NFC reader found: ", e)

    print("Initing codec")
    i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA)
    codec.init(i2c)

    print("Initing Canopy")
    canopy.init([fern.LED1_DATA, fern.LED2_DATA], 100)
    asyncio.create_task(render_loop())

    print("Starting audio loop")
    asyncio.create_task(play_audio_loop(audio_out))

    print("Starting input loop")
    asyncio.create_task(input_loop())

    asyncio.get_event_loop().run_forever()


asyncio.run(main())
