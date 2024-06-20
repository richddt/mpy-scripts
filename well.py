from machine import SPI, I2C, Pin, I2S
import fern
import codec
import json
import canopy
import nfc
import asyncio
from fps import FPS
from tween import tween
import mixer
import rotenc
from ucollections import namedtuple

PatternRainbow = "CTP-eyJpZCI6ImZjNjBlMzlkLThiNDYtNGVkMS1iNTM2LTc1M2QzNDQ3MDc0YiIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjE1LFsxLDEsMF1dLFswLjMsWzAsMSwwXV0sWzAuNSxbMCwxLDFdXSxbMC43LFswLDAsMV1dLFswLjg1LFsxLDAsMV1dLFsxLFsxLDAsMF1dXSwiX2JsYWNrLXdoaXRlIjpbWzAsWzAsMCwwXV0sWzEsWzEsMSwxXV1dfSwicGFyYW1zIjp7fSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOjEsImJsZW5kIjoibm9ybWFsIiwicGFsZXR0ZSI6InByaW1hcnkiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuNDMsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fV19"
PatternBlue = "CTP-eyJpZCI6IjNmNDdmYjAwLWFlYTgtNDEwYy1hMzk2LTEwYmY3Yjc0NDA2MyIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAsMC4xMzMzMzMzMzMzMzMzMzMzMywxXV0sWzAuNSxbMCwwLjE2ODYyNzQ1MDk4MDM5MjE3LDFdXSxbMSxbMCwwLDFdXV19LCJwYXJhbXMiOnsiaW11LnNoYWtlIjowfSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOnsidHlwZSI6InNpbiIsImlucHV0cyI6eyJ2YWx1ZSI6MC41NywibWluIjowLjMyLCJtYXgiOjF9fSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuMjcsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNTQsInJvdGF0aW9uIjowfX0seyJlZmZlY3QiOiJzcGFya2xlcyIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im11bHRpcGx5IiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuMTMsIm9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX1dfQ"
PatternRed = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMC4wMSxbMCwwLDBdXSxbMC4wNyxbMSwwLDBdXSxbMC4yNyxbMC44MTE3NjQ3MDU4ODIzNTI5LDAuNjUwOTgwMzkyMTU2ODYyOCwwXV0sWzAuNTMsWzEsMCwwLjAzMTM3MjU0OTAxOTYwNzg0XV0sWzAuNzcsWzEsMC4zNDkwMTk2MDc4NDMxMzcyNCwwXV0sWzAuOTMsWzEsMCwwXV0sWzAuOTgsWzAsMCwwXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0Ijoic3BhcmtsZXMiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuODUsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX0seyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MC4wOCwibWF4IjowLjQ0fX0sInNpemUiOjAuNzUsInJvdGF0aW9uIjowfX1dfQ"
PatternPurple = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMCxbMSwwLDBdXSxbMC4zMSxbMC42MDc4NDMxMzcyNTQ5MDE5LDAsMC44MTE3NjQ3MDU4ODIzNTI5XV0sWzAuNSxbMCwwLDAuODkwMTk2MDc4NDMxMzcyNV1dLFswLjc2LFswLjUzMzMzMzMzMzMzMzMzMzMsMCwxXV0sWzAuOTgsWzEsMCwwXV1dLCJQYWxldHRlMiI6W1swLFsxLDAuOTg4MjM1Mjk0MTE3NjQ3MSwwLjkwMTk2MDc4NDMxMzcyNTVdXSxbMSxbMSwwLjg5NDExNzY0NzA1ODgyMzYsMC4xODAzOTIxNTY4NjI3NDUxXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fSx7ImVmZmVjdCI6InNwYXJrbGVzIiwib3BhY2l0eSI6ImltdS5zaGFrZSIsImJsZW5kIjoibm9ybWFsLW5vbmJsYWNrIiwicGFsZXR0ZSI6IlBhbGV0dGUyIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuNTEsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX19fV19"

PatternIdle = "CTP-eyJpZCI6IjFiMjFhMTUwLTliZWMtNDQwOS04NzVmLWJiZjIwZDliNWQxNSIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMC44Mjc0NTA5ODAzOTIxNTY4LDAuNl1dXX0sInBhcmFtcyI6e30sImxheWVycyI6W3siZWZmZWN0Ijoic29saWQiLCJvcGFjaXR5Ijp7InR5cGUiOiJzaW4iLCJpbnB1dHMiOnsidmFsdWUiOjAuNCwibWluIjowLjA1LCJtYXgiOjAuNDR9fSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0IjowLjV9fV19"
PatternProgress = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicCI6W1swLFsxLDEsMV1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiY2hhc2VyIiwib3BhY2l0eSI6MSwiYmxlbmQiOiJtdWx0aXBseSIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6InByb2dyZXNzIiwic2l6ZSI6MX19XX0"

alpha = tween()

m = mixer.Mixer()
VoiceWell = mixer.Voice("/well.wav")

ModeSwitch = rotenc.RotarySwitch(
    [(fern.D1, "rainbow"), (fern.D2, "blue"), (fern.D3, "red"), (fern.D4, "purple")]
)

pattern_active = canopy.Pattern(PatternIdle)
pattern_idle = canopy.Pattern(PatternIdle)
pattern_progress = canopy.Pattern(PatternProgress)

Mode = namedtuple("Mode", ["name", "pattern"])
modes = [
    Mode("rainbow", PatternRainbow),
    Mode("blue", PatternBlue),
    Mode("red", PatternRed),
    Mode("purple", PatternPurple),
]
current_mode = "rainbow"


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
        print("Tag found ", reader.tag)
        m.play(VoiceWell)
        alpha.tween(1, 0.8)

        try:
            tag = await reader.readNdef()
            for r in tag.records:
                # strip off the language code
                decoded = r.payload[3:].decode("utf-8")
                if "set:" in decoded:
                    set_mode(decoded.split(":")[1])

        except Exception as e:
            print("Error reading tag: ", e)
            # we get here if e.g tag isn't formatted
            pass

        # these will a no-op for NFC cards that aren't the orbs
        await reader.enableMailbox()
        await reader.writeMessage(current_mode)

        while True:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        alpha.tween(0, 2)
        print("Tag lost")


async def render_loop():
    seg_front = canopy.Segment(0, 0, 60)
    seg_back = canopy.Segment(1, 0, 40)
    # seg_back_left = canopy.Segment(1, 0, 19)
    # seg_back_right = canopy.Segment(1, 19, 19, True)

    # pattern_active = canopy.Pattern(PatternRed)
    # pattern_idle = canopy.Pattern(PatternBlue)

    alpha.tween(0, 0)
    f = FPS(verbose=True)
    p = canopy.Params()
    while True:
        f.tick()
        canopy.clear()
        a = float(alpha)
        p["progress"] = a
        if a > 0.0:
            canopy.draw(seg_front, pattern_active)
            canopy.draw(seg_front, pattern_progress, params=p)
        canopy.draw(seg_front, pattern_idle, 1.0 - a)
        canopy.draw(seg_back, pattern_active, max(a, 0.1))
        canopy.render()
        await asyncio.sleep(0.001)


async def play_audio_loop(audio_out):
    swriter = asyncio.StreamWriter(audio_out)
    wav_samples = bytearray(10000)
    wav_samples_mv = memoryview(wav_samples)

    while True:
        m.mixinto(wav_samples_mv)
        swriter.out_buf = wav_samples_mv[:]
        await swriter.drain()


async def input_loop():
    previous_mode = None
    while True:
        ModeSwitch.tick()
        mode = ModeSwitch.value
        if mode != previous_mode:
            previous_mode = mode
            set_mode(mode)

        await asyncio.sleep(0.2)


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
        ibuf=6000,
    )

    # print("Mounting SD card")
    # fern.mount_sdcard()

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
    canopy.init([fern.LED1_DATA, fern.LED2_DATA], 60)
    asyncio.create_task(render_loop())

    print("Starting audio loop")
    asyncio.create_task(play_audio_loop(audio_out))

    print("Starting input loop")
    asyncio.create_task(input_loop())

    asyncio.get_event_loop().run_forever()


asyncio.run(main())
