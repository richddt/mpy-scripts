import asyncio
from machine import SPI, I2C, Pin
import fern
import nfc
import ndef
import canopy
from fps import FPS
from tween import tween
import espnow
import network
from ucollections import namedtuple
from debounced_input import DebouncedInput

TagFound = False

PatternRainbow = "CTP-eyJpZCI6IjE5NjEyMDE1LTFjMWEtNDk0Zi04YTFkLTA3YWI4NGUyM2MyYSIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjA5LFsxLDAsMF1dLFswLjIzLFsxLDEsMF1dLFswLjM4LFswLDEsMF1dLFswLjUsWzAsMSwxXV0sWzAuNjgsWzAsMCwxXV0sWzAuODMsWzEsMCwxXV0sWzEsWzEsMCwwXV1dfSwicGFyYW1zIjp7fSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOjAuNSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoicHJpbWFyeSIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InNhdyIsImlucHV0cyI6eyJ2YWx1ZSI6MC4zMywibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC42LCJyb3RhdGlvbiI6MH19XX0"
PatternBlue = "CTP-eyJpZCI6IjNmNDdmYjAwLWFlYTgtNDEwYy1hMzk2LTEwYmY3Yjc0NDA2MyIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAsMC4xMzMzMzMzMzMzMzMzMzMzMywxXV0sWzAuNSxbMCwwLjE2ODYyNzQ1MDk4MDM5MjE3LDFdXSxbMSxbMCwwLDFdXV19LCJwYXJhbXMiOnsiaW11LnNoYWtlIjowfSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOnsidHlwZSI6InNpbiIsImlucHV0cyI6eyJ2YWx1ZSI6MC41NywibWluIjowLjMyLCJtYXgiOjF9fSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuMjcsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNTQsInJvdGF0aW9uIjowfX0seyJlZmZlY3QiOiJzcGFya2xlcyIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im11bHRpcGx5IiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuMTMsIm9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX1dfQ"
PatternRed = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMC4wMSxbMCwwLDBdXSxbMC4wNyxbMSwwLDBdXSxbMC4yNyxbMC44MTE3NjQ3MDU4ODIzNTI5LDAuNjUwOTgwMzkyMTU2ODYyOCwwXV0sWzAuNTMsWzEsMCwwLjAzMTM3MjU0OTAxOTYwNzg0XV0sWzAuNzcsWzEsMC4zNDkwMTk2MDc4NDMxMzcyNCwwXV0sWzAuOTMsWzEsMCwwXV0sWzAuOTgsWzAsMCwwXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0Ijoic3BhcmtsZXMiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuODUsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX0seyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MC4wOCwibWF4IjowLjQ0fX0sInNpemUiOjAuNzUsInJvdGF0aW9uIjowfX1dfQ"
PatternPurple = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMCxbMSwwLDBdXSxbMC4zMSxbMC42MDc4NDMxMzcyNTQ5MDE5LDAsMC44MTE3NjQ3MDU4ODIzNTI5XV0sWzAuNSxbMCwwLDAuODkwMTk2MDc4NDMxMzcyNV1dLFswLjc2LFswLjUzMzMzMzMzMzMzMzMzMzMsMCwxXV0sWzAuOTgsWzEsMCwwXV1dLCJQYWxldHRlMiI6W1swLFsxLDAuOTg4MjM1Mjk0MTE3NjQ3MSwwLjkwMTk2MDc4NDMxMzcyNTVdXSxbMSxbMSwwLjg5NDExNzY0NzA1ODgyMzYsMC4xODAzOTIxNTY4NjI3NDUxXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fSx7ImVmZmVjdCI6InNwYXJrbGVzIiwib3BhY2l0eSI6ImltdS5zaGFrZSIsImJsZW5kIjoibm9ybWFsLW5vbmJsYWNrIiwicGFsZXR0ZSI6IlBhbGV0dGUyIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuNTEsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX19fV19"

alpha = tween()

Mode = namedtuple("Mode", ["name", "pattern"])
modes = [
    Mode("rainbow", PatternRainbow),
    Mode("blue", PatternBlue),
    Mode("red", PatternRed),
    Mode("purple", PatternPurple),
]
current_mode = modes[0]
current_pattern = canopy.Pattern(current_mode.pattern)


async def tag_found(reader):
    global TagFound, alpha
    try:
        print("Tag found ", reader.tag)
        TagFound = True
        alpha.tween(1, 0.3)

        # print("Sending message")
        # await reader.writeMessage("Hello from fern")

        try:
            found = False
            existing = ""
            print("Reading NFC tag")
            ndefmsg = await reader.readNdef()
            for r in ndefmsg.records:
                print(r)
                if r.id == b"CT":
                    print("Found CT record")
                    found = True
                    existing = r.payload[3:].decode("utf-8")
                    break
            if not found:
                r = ndef.NdefRecord()
                ndefmsg.records.append(r)

            print("Existing tag payload: ", existing)

            if existing == "red" and current_mode.name == "blue":
                new_payload = "purple"
            elif existing == "blue" and current_mode.name == "red":
                new_payload = "purple"
            else:
                new_payload = current_mode.name

            print("New tag payload: ", new_payload)
            if existing != new_payload:
                r.tnf = ndef.TNF_WELL_KNOWN
                r.set_type(ndef.RTD_TEXT)
                r.set_id(b"CT")
                r.set_payload(b"\x02en" + bytes(new_payload, "utf-8"))
                ndefmsg.fix()
                await reader.writeNdef(ndefmsg)
                print(f"Updated tag with => {new_payload}")

        except Exception as e:
            print(e)
            print("Error updating NFC tag with new payload")

        while True:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        alpha.tween(0.2, 0.3)
        TagFound = False
        print("Tag lost")


async def render_loop():
    global current_pattern, alpha
    # seg = canopy.Segment(0, 0, 24)
    seg = canopy.Segment(0, 0, 40)

    # p = canopy.Pattern(PatternTornado)

    # pattern_base = canopy.Pattern(PatternPipe)
    # pattern_pipe = canopy.Pattern(PatternPipe)
    # pattern_tornado = canopy.Pattern(PatternTornado)

    f = FPS(verbose=True)
    while True:
        f.tick()
        canopy.clear()
        canopy.draw(seg, current_pattern, alpha)
        canopy.render()
        await asyncio.sleep(0)


async def beacon():
    # init espnow
    e = espnow.ESPNow()
    network.WLAN(network.STA_IF).active(True)
    e.active(True)
    bcast = b"\xFF" * 6
    e.add_peer(bcast)

    while True:
        # TODO: the beacon should depend on the mode of this device
        e.send(bcast, current_mode.name)
        await asyncio.sleep(0.3)


def button_callback(btn):
    global current_mode
    global current_pattern
    if btn.pressed():
        current_mode = modes[(modes.index(current_mode) + 1) % len(modes)]
        current_pattern = canopy.Pattern(current_mode.pattern)
        print("Switching to mode: ", current_mode.name)


async def main():
    # read our current mode from storage?
    alpha.tween(0.2, 0.3)
    btn = DebouncedInput(fern.D8, button_callback, Pin.PULL_UP, False, 50)

    print("Opening NFC reader")
    spi = SPI(
        1, baudrate=7000000, sck=fern.NFC_SCK, mosi=fern.NFC_MOSI, miso=fern.NFC_MISO
    )
    reader = nfc.NfcReader(spi, fern.NFC_NSS, fern.NFC_BUSY, fern.NFC_RST)
    reader.onTagFound(tag_found)
    try:
        await reader.start(verbose=True)
        asyncio.create_task(reader.loop())
    except Exception as e:
        print("No NFC reader found: ", e)

    i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA)

    # print("Initing codec")
    # codec.init(i2c)

    # print("Mount SD card")
    # mounted = False
    # try:
    #     sd = fern.sdcard()
    #     os.mount(sd, "/sd")
    #     mounted = True
    # except:
    #     print("No SD card found")

    # if mounted:
    #     print("Initing I2S audio out")
    #     audio_out = I2S(
    #         0,
    #         sck=Pin(fern.I2S_BCK),
    #         ws=Pin(fern.I2S_WS),
    #         sd=Pin(fern.I2S_SDOUT),
    #         mck=Pin(fern.I2S_MCK),
    #         mode=I2S.TX,
    #         bits=16,
    #         format=I2S.STEREO,
    #         rate=16000,
    #         ibuf=4000,
    #     )
    #     WAV_FILE = "test.wav"
    #     try:
    #         wav = open("/sd/{}".format(WAV_FILE), "rb")
    #         asyncio.create_task(continuous_play(audio_out, wav))
    #     except:
    #         print("Can't open WAV file: ", WAV_FILE)

    canopy.init([fern.LED1_DATA, fern.LED2_DATA], 200)
    asyncio.create_task(render_loop())

    asyncio.create_task(beacon())

    asyncio.get_event_loop().run_forever()


asyncio.run(main())
