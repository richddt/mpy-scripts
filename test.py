import os
from machine import Pin, SPI, I2C, I2S
import asyncio
import fern
import nfc
import seesaw
import canopy
import codec
from fps import FPS
from tween import tween

# PatternRainbow = "CTP-eyJpZCI6IjAzNWVlN2NjLWZiM2MtNDI0Ni1hOTM1LTdjNGQ3ZDYyMzEyMyIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMCwwXV0sWzAuMTksWzAuOTY0NzA1ODgyMzUyOTQxMiwxLDBdXSxbMC4zNixbMC4wNjI3NDUwOTgwMzkyMTU2OSwxLDAuMDUwOTgwMzkyMTU2ODYyNzQ0XV0sWzAuNTEsWzAsMSwwLjg3MDU4ODIzNTI5NDExNzddXSxbMC42NyxbMCwwLjA5MDE5NjA3ODQzMTM3MjU1LDFdXSxbMC44MixbMC40OCwwLjAxLDAuNDJdXSxbMC45OSxbMSwwLDBdXV19LCJwYXJhbXMiOnt9LCJsYXllcnMiOlt7ImVmZmVjdCI6ImdyYWRpZW50Iiwib3BhY2l0eSI6MSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJyc2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjQxLCJtaW4iOjAsIm1heCI6MX19LCJzaXplIjowLjUsInJvdGF0aW9uIjowfX1dfQ"
# PatternRainbow = "CTP-eyJpZCI6IjAzNWVlN2NjLWZiM2MtNDI0Ni1hOTM1LTdjNGQ3ZDYyMzEyMyIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMCwwXV0sWzAuMTksWzAuOTY0NzA1ODgyMzUyOTQxMiwxLDBdXSxbMC4zNixbMC4wNjI3NDUwOTgwMzkyMTU2OSwxLDAuMDUwOTgwMzkyMTU2ODYyNzQ0XV0sWzAuNTEsWzAsMSwwLjg3MDU4ODIzNTI5NDExNzddXSxbMC42NyxbMCwwLjA5MDE5NjA3ODQzMTM3MjU1LDFdXSxbMC44MixbMC40OCwwLjAxLDAuNDJdXSxbMC45OSxbMSwwLDBdXV19LCJwYXJhbXMiOnsicHJvZ3Jlc3MiOjB9LCJsYXllcnMiOlt7ImVmZmVjdCI6ImdyYWRpZW50Iiwib3BhY2l0eSI6InByb2dyZXNzIiwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJyc2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjQxLCJtaW4iOjAsIm1heCI6MX19LCJzaXplIjowLjUsInJvdGF0aW9uIjowfX1dfQ"
# SparklyRainbow = "CTP-eyJpZCI6ImViOWY0OTZjLTY5ZDYtNDVlYy05NTQ5LTEyZTI1ZjY4ZTg0OCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMCwwXV0sWzAuMTksWzEsMC45MzMzMzMzMzMzMzMzMzMzLDBdXSxbMC4zNyxbMCwxLDAuMDgyMzUyOTQxMTc2NDcwNTldXSxbMC41NCxbMCwwLjk4NDMxMzcyNTQ5MDE5NiwxXV0sWzAuNjgsWzAsMC4wNTA5ODAzOTIxNTY4NjI3NDQsMV1dLFswLjg1LFsxLDAsMC44ODIzNTI5NDExNzY0NzA2XV0sWzEsWzEsMCwwXV1dLCJQYWxldHRlMiI6W1swLFswLDAsMF1dLFsxLFsxLDAuOTUyOTQxMTc2NDcwNTg4MiwwLjQxOTYwNzg0MzEzNzI1NDldXV19LCJwYXJhbXMiOnsic3BhcmtsZSI6MC4xOH0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJQYWxldHRlMSIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuMjQsIm1pbiI6MCwibWF4lIjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fSx7ImVmZmVjdCI6InNwYXJrbGVzIiwib3BhY2l0eSI6MSwiYmxlbmQiOiJub3JtYWwtbm9uYmxhY2siLCJwYWxldHRlIjoiUGFsZXR0ZTIiLCJpbnB1dHMiOnsiZGVuc2l0eSI6InNwYXJrbGUiLCJvZmZzZXQiOnsidHlwZSI6InNpbiIsImlucHV0cyI6eyJ2YWx1ZSI6MC41LCJtaW4iOjAsIm1heCI6MX19fX1dfQ"
# PatternPipe = "CTP-eyJpZCI6IjQ3N2QwYzFkLTBhMDMtNGFiNS1hYjY0LTE2ZDRlOTNlZWMyMCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAuNTE3NjQ3MDU4ODIzNTI5NSwwLDFdXSxbMC4yMyxbMC4zNSwwLDFdXSxbMC40OSxbMC43NDkwMTk2MDc4NDMxMzczLDAsMV1dLFswLjc0LFsxLDAsMC4wMTU2ODYyNzQ1MDk4MDM5Ml1dLFsxLFswLjQ4MjM1Mjk0MTE3NjQ3MDYsMCwxXV1dLCJQYWxldHRlMiI6W1swLFsxLDEsMV1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MX0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5Ijp7InR5cGUiOiJzaW4iLCJpbnB1dHMiOnsidmFsdWUiOjAuNTgsIm1pbiI6MC40OSwibWF4IjoxfX0sImJsZW5kIjoibm9ybWFsIiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoicnNhdyIsImlucHV0cyI6eyJ2YWx1ZSI6MC40MywibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC41LCJyb3RhdGlvbiI6MH19LHsiZWZmZWN0IjoiY2hhc2VyIiwib3BhY2l0eSI6MSwiYmxlbmQiOiJtYXNrIiwicGFsZXR0ZSI6IlBhbGV0dGUyIiwiaW5wdXRzIjp7Im9mZnNldCI6InByb2dyZXNzIiwic2l6ZSI6MC41fX1dfQ"
# PatternTornado = "CTP-eyJpZCI6IjQ3N2QwYzFkLTBhMDMtNGFiNS1hYjY0LTE2ZDRlOTNlZWMyMCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAuNTE3NjQ3MDU4ODIzNTI5NSwwLDFdXSxbMC4yMyxbMC4zNSwwLDFdXSxbMC40OSxbMC43NDkwMTk2MDc4NDMxMzczLDAsMV1dLFswLjc0LFsxLDAsMC4wMTU2ODYyNzQ1MDk4MDM5Ml1dLFsxLFswLjQ4MjM1Mjk0MTE3NjQ3MDYsMCwxXV1dLCJQYWxldHRlMiI6W1swLFsxLDAuOTkyMTU2ODYyNzQ1MDk4MSwwLjUyMTU2ODYyNzQ1MDk4MDRdXV19LCJwYXJhbXMiOnt9LCJsYXllcnMiOlt7ImVmZmVjdCI6ImdyYWRpZW50Iiwib3BhY2l0eSI6MC43LCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJQYWxldHRlMSIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuNDMsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fSx7ImVmZmVjdCI6ImNoYXNlciIsIm9wYWNpdHkiOjAuNywiYmxlbmQiOiJub3JtYWwtbm9uYmxhY2siLCJwYWxldHRlIjoiUGFsZXR0ZTIiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuNiwibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC4wN319XX0"


PatternProgress = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicCI6W1swLFsxLDEsMV1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiY2hhc2VyIiwib3BhY2l0eSI6MSwiYmxlbmQiOiJtdWx0aXBseSIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6InByb2dyZXNzIiwic2l6ZSI6MX19XX0"
PatternRainbow = "CTP-eyJpZCI6IjE5NjEyMDE1LTFjMWEtNDk0Zi04YTFkLTA3YWI4NGUyM2MyYSIsInZlcnNpb24iOjEsIm5hbWUiOiJ0ZXN0IiwicGFsZXR0ZXMiOnsicHJpbWFyeSI6W1swLFsxLDAsMF1dLFswLjA5LFsxLDAsMF1dLFswLjIzLFsxLDEsMF1dLFswLjM4LFswLDEsMF1dLFswLjUsWzAsMSwxXV0sWzAuNjgsWzAsMCwxXV0sWzAuODMsWzEsMCwxXV0sWzEsWzEsMCwwXV1dfSwicGFyYW1zIjp7fSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOjAuNSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoicHJpbWFyeSIsImlucHV0cyI6eyJvZmZzZXQiOnsidHlwZSI6InNhdyIsImlucHV0cyI6eyJ2YWx1ZSI6MC4zMywibWluIjowLCJtYXgiOjF9fSwic2l6ZSI6MC42LCJyb3RhdGlvbiI6MH19XX0"
PatternBlue = "CTP-eyJpZCI6IjNmNDdmYjAwLWFlYTgtNDEwYy1hMzk2LTEwYmY3Yjc0NDA2MyIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzAsMC4xMzMzMzMzMzMzMzMzMzMzMywxXV0sWzAuNSxbMCwwLjE2ODYyNzQ1MDk4MDM5MjE3LDFdXSxbMSxbMCwwLDFdXV19LCJwYXJhbXMiOnsiaW11LnNoYWtlIjowfSwibGF5ZXJzIjpbeyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOnsidHlwZSI6InNpbiIsImlucHV0cyI6eyJ2YWx1ZSI6MC41NywibWluIjowLjMyLCJtYXgiOjF9fSwiYmxlbmQiOiJub3JtYWwiLCJwYWxldHRlIjoiUGFsZXR0ZTEiLCJpbnB1dHMiOnsib2Zmc2V0Ijp7InR5cGUiOiJzYXciLCJpbnB1dHMiOnsidmFsdWUiOjAuMjcsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNTQsInJvdGF0aW9uIjowfX0seyJlZmZlY3QiOiJzcGFya2xlcyIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im11bHRpcGx5IiwicGFsZXR0ZSI6IlBhbGV0dGUxIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuMTMsIm9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX1dfQ"
PatternRed = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMC4wMSxbMCwwLDBdXSxbMC4wNyxbMSwwLDBdXSxbMC4yNyxbMC44MTE3NjQ3MDU4ODIzNTI5LDAuNjUwOTgwMzkyMTU2ODYyOCwwXV0sWzAuNTMsWzEsMCwwLjAzMTM3MjU0OTAxOTYwNzg0XV0sWzAuNzcsWzEsMC4zNDkwMTk2MDc4NDMxMzcyNCwwXV0sWzAuOTMsWzEsMCwwXV0sWzAuOTgsWzAsMCwwXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0Ijoic3BhcmtsZXMiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuODUsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjI2LCJtaW4iOjAsIm1heCI6MX19fX0seyJlZmZlY3QiOiJncmFkaWVudCIsIm9wYWNpdHkiOiJpbXUuc2hha2UiLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MC4wOCwibWF4IjowLjQ0fX0sInNpemUiOjAuNzUsInJvdGF0aW9uIjowfX1dfQ"
PatternPurple = "CTP-eyJpZCI6IjAzYzRhOTdiLWEzMzUtNGI1OC1iMTU2LTczYjU5MWNhMmQ0NCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7InAiOltbMCxbMSwwLDBdXSxbMC4zMSxbMC42MDc4NDMxMzcyNTQ5MDE5LDAsMC44MTE3NjQ3MDU4ODIzNTI5XV0sWzAuNSxbMCwwLDAuODkwMTk2MDc4NDMxMzcyNV1dLFswLjc2LFswLjUzMzMzMzMzMzMzMzMzMzMsMCwxXV0sWzAuOTgsWzEsMCwwXV1dLCJQYWxldHRlMiI6W1swLFsxLDAuOTg4MjM1Mjk0MTE3NjQ3MSwwLjkwMTk2MDc4NDMxMzcyNTVdXSxbMSxbMSwwLjg5NDExNzY0NzA1ODgyMzYsMC4xODAzOTIxNTY4NjI3NDUxXV1dfSwicGFyYW1zIjp7ImltdS5zaGFrZSI6MH0sImxheWVycyI6W3siZWZmZWN0IjoiZ3JhZGllbnQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJwIiwiaW5wdXRzIjp7Im9mZnNldCI6eyJ0eXBlIjoic2F3IiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX0sInNpemUiOjAuNSwicm90YXRpb24iOjB9fSx7ImVmZmVjdCI6InNwYXJrbGVzIiwib3BhY2l0eSI6ImltdS5zaGFrZSIsImJsZW5kIjoibm9ybWFsLW5vbmJsYWNrIiwicGFsZXR0ZSI6IlBhbGV0dGUyIiwiaW5wdXRzIjp7ImRlbnNpdHkiOjAuNTEsIm9mZnNldCI6eyJ0eXBlIjoic2luIiwiaW5wdXRzIjp7InZhbHVlIjowLjUsIm1pbiI6MCwibWF4IjoxfX19fV19"


TagFound = False
current_tag = ""
current_pattern = None

ProgressTween = tween(0, 0)

TornadoPin = Pin(fern.LED1_CLOCK, Pin.OUT, value=0)


async def tag_found(reader):
    global TagFound
    global ProgressTween
    global current_tag, current_pattern

    print("Tag found ", reader.tag)

    try:
        ProgressTween.tween(1, 2)
        TagFound = True
        current_pattern = None

        try:
            ndefmsg = await reader.readNdef()
            for r in ndefmsg.records:
                print(r)
                # if r.id == b"CT":
                current_tag = r.payload[3:].decode("utf-8")
                print("Found a canopy tag", current_tag)
                current_pattern = canopy.Pattern(
                    {
                        "red": PatternRed,
                        "blue": PatternBlue,
                        "purple": PatternPurple,
                    }.get(current_tag, PatternRainbow)
                )
                if current_tag == "purple":
                    TornadoPin.value(1)
        except Exception as e:
            pass

        while True:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        ProgressTween.tween(0, 0.5)
        TagFound = False
        TornadoPin.value(0)
        print("Tag lost")


async def encoder_loop(ss):
    last = await ss.encoder_position()
    print("Encoder: ", last)
    while True:
        value = await ss.encoder_position()
        if value != last:
            print("Encoder: ", value)
            last = value
        await asyncio.sleep(0.1)


async def render_loop():
    seg_pipe = canopy.Segment(1, 0, 50)
    seg_tornado = canopy.Segment(0, 0, 16)
    seg_base = canopy.Segment(2, 0, 15)

    # pattern_base = canopy.Pattern(PatternPipe)
    # pattern_pipe = canopy.Pattern(PatternPipe)
    # pattern_tornado = canopy.Pattern(PatternTornado)

    # pattern_pipe.params["progress"] = ProgressTween
    # pattern_base.params["progress"] = 1

    pattern_progress = canopy.Pattern(PatternProgress)
    params = canopy.Params()
    # pattern_progress.params["progress"] = ProgressTween

    last = 0
    f = FPS(verbose=True)
    while True:
        # value = encoder.encoder_position()
        # if value != last:
        #     pattern.params["progress"] += (last - value) / 50.0
        #     last = value
        #     if pattern.params["progress"] > 1:
        #         pattern.params["progress"] = 1
        #     if pattern.params["progress"] < 0:
        #         pattern.params["progress"] = 0

        if current_pattern is None:
            await asyncio.sleep(0.1)
            continue

        f.tick()
        params["progress"] = float(ProgressTween)
        canopy.clear()
        if TagFound:
            canopy.draw(seg_base, current_pattern)
        canopy.draw(seg_pipe, current_pattern)
        canopy.draw(seg_pipe, pattern_progress, params)
        if float(ProgressTween) == 1.0 and current_tag == "purple":
            canopy.draw(seg_tornado, current_pattern)
        canopy.render()
        await asyncio.sleep(0)


async def continuous_play(audio_out, wav):
    swriter = asyncio.StreamWriter(audio_out)

    _ = wav.seek(44)  # advance to first byte of Data section in WAV file

    # allocate sample array
    # memoryview used to reduce heap allocation
    wav_samples = bytearray(10000)
    wav_samples_mv = memoryview(wav_samples)

    # continuously read audio samples from the WAV file
    # and write them to an I2S DAC
    print("==========  START PLAYBACK ==========")

    while True:
        num_read = wav.readinto(wav_samples_mv)
        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            _ = wav.seek(44)
        else:
            # apply temporary workaround to eliminate heap allocation in uasyncio Stream class.
            # workaround can be removed after acceptance of PR:
            #    https://github.com/micropython/micropython/pull/7868
            # swriter.write(wav_samples_mv[:num_read])
            swriter.out_buf = wav_samples_mv[:num_read]
            await swriter.drain()


async def main():
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
        raise

    i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA)

    # address of rotenc is 0x36 + up to 7
    # digital IO for button is 24

    print("Initing encoder")
    encoder = seesaw.Seesaw(i2c, 0x36)
    try:
        await encoder.start()
        asyncio.create_task(encoder_loop(encoder))
    except:
        print("No encoder found")

    print("Initing codec")
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

    print("Starting canopy")
    D1 = 1
    canopy.init([fern.LED1_DATA, fern.LED2_DATA, D1], 100)
    canopy.clear()
    canopy.render()
    asyncio.create_task(render_loop())

    asyncio.get_event_loop().run_forever()


asyncio.run(main())


# already_added = False
# try:
#     ndefmsg = self.readNdef()
#     print("Ndef message:")
#     for r in ndefmsg.records:
#         if r.id == b"CT":
#             already_added = True
#         print(r.payload)
# except:
#     ndefmsg = ndef.new_message(
#         (ndef.TNF_WELL_KNOWN, ndef.RTD_TEXT, "", b"\x02enboooom")
#     )

# if not already_added:
#     print("Adding record")
#     r = ndef.NdefRecord()
#     r.tnf = ndef.TNF_WELL_KNOWN
#     r.set_type(ndef.RTD_TEXT)
#     r.set_id(b"CT")
#     r.set_payload(b"\x02enPlease work")

#     ndefmsg.records.append(r)
#     ndefmsg.fix()
#     self.writeNdef(ndefmsg)
#     print("Added")
