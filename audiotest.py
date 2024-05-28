import os, sys
from machine import Pin, SPI, I2C, I2S
import asyncio
import fern
import canopy
import seesaw
import codec
import mixer
import math, time
from fps import FPS
from debounced_input import DebouncedInput


PatternRedYellowGreen = "CTP-eyJpZCI6IjMzNzIzOGZjLTIyMTEtNDlhZS04MTQwLWFmMDIyNDAxMGZlOCIsInZlcnNpb24iOjEsIm5hbWUiOiJOZXcgUGF0dGVybiIsInBhbGV0dGVzIjp7IlBhbGV0dGUxIjpbWzAsWzEsMCwwXV0sWzAuMixbMSwwLDBdXSxbMC41MixbMSwwLjkyNTQ5MDE5NjA3ODQzMTQsMF1dLFsxLFswLDEsMC4wMTU2ODYyNzQ1MDk4MDM5Ml1dXX0sInBhcmFtcyI6eyJwcm9ncmVzcyI6MC42OH0sImxheWVycyI6W3siZWZmZWN0Ijoic29saWQiLCJvcGFjaXR5IjoxLCJibGVuZCI6Im5vcm1hbCIsInBhbGV0dGUiOiJQYWxldHRlMSIsImlucHV0cyI6eyJvZmZzZXQiOiJwcm9ncmVzcyJ9fV19"

fern.mount_sdcard()
coin = mixer.Voice("/sd/coin16.wav")
coin.volume = 0.8

m = mixer.Mixer()


async def render_loop():
    s = canopy.Segment(0, 0, 100)
    pattern = canopy.Pattern(PatternRedYellowGreen)
    f = FPS(verbose=True)
    while True:
        f.tick()
        canopy.clear()
        canopy.draw(s, pattern)
        canopy.render()
        await asyncio.sleep(0.001)


# async def continuous_play(audio_out):
#     swriter = asyncio.StreamWriter(audio_out)

#     voice = mixer.Voice("/sd/test.wav")
#     voice.loop = True
#     voice.volume = 0.1

#     # allocate sample array
#     # memoryview used to reduce heap allocation
#     wav_samples = bytearray(5000)
#     wav_samples_mv = memoryview(wav_samples)

#     # continuously read audio samples from the WAV file
#     # and write them to an I2S DAC
#     print("==========  START PLAYBACK ==========")

#     while True:
#         # volume is a sin wave
#         voice.volume = 0.5 + 0.5 * math.sin(time.ticks_ms() / 1000)
#         mixer.mixinto(voice, wav_samples_mv)
#         # apply temporary workaround to eliminate heap allocation in uasyncio Stream class.
#         # workaround can be removed after acceptance of PR:
#         #    https://github.com/micropython/micropython/pull/7868
#         # swriter.write(wav_samples_mv[:num_read])
#         swriter.out_buf = wav_samples_mv[:]
#         await swriter.drain()


# async def connect_stdin_stdout():
#     loop = asyncio.get_event_loop()
#     reader = asyncio.StreamReader(sys.stdin)
#     return reader
#     #protocol = asyncio.StreamReaderProtocol(reader)
#     #await loop.connect_read_pipe(lambda: protocol, sys.stdin)
#     #w_transport, w_protocol = await loop.connect_write_pipe(
#     #    asyncio.streams.FlowControlMixin, sys.stdout
#     #)
#     #writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
#     return reader, writer


async def continuous_play(audio_out):
    swriter = asyncio.StreamWriter(audio_out)
    wav_samples = bytearray(4096)
    wav_samples_mv = memoryview(wav_samples)
    # w = open("/sd/bg.wav", "rb")
    voice = mixer.Voice("/sd/bg.wav")
    voice.loop = True
    voice.volume = 1.0
    voice.play()

    m.play(voice)

    print("Added voices")

    while True:
        print(m.voices())
        m.mixinto(wav_samples_mv)
        # apply temporary workaround to eliminate heap allocation in uasyncio Stream class.
        # workaround can be removed after acceptance of PR:
        #    https://github.com/micropython/micropython/pull/7868
        # swriter.write(wav_samples_mv[:num_read])
        swriter.out_buf = wav_samples_mv[:]
        await swriter.drain()


async def encoder_loop(ss):
    last = await ss.encoder_position()
    print("Encoder: ", last)
    while True:
        value = await ss.encoder_position()
        if value != last:
            print("Encoder: ", value)
            last = value
        await asyncio.sleep(0.05)


def button_callback(btn):
    if btn.pressed():
        print("Playing coin")
        m.play(coin)


async def main():
    i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA, freq=100000)
    print(i2c.scan())

    btn = DebouncedInput(fern.D8, button_callback, Pin.PULL_UP, False, 50)

    # print("Initing encoder")
    # encoder = seesaw.Seesaw(i2c, 0x36)
    # try:
    #     await encoder.start()
    #     asyncio.create_task(encoder_loop(encoder))
    # except:
    #     print("No encoder found")

    # canopy.init([fern.LED1_DATA, fern.LED2_DATA], 100)
    # canopy.clear()
    # canopy.render()

    audio_out = None

    print("Initing codec")
    codec.init(i2c)
    time.sleep_ms(1000)
    # codec.dumpregisters(i2c)

    print("Initing I2S audio out")
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
        ibuf=4000,
    )

    asyncio.create_task(continuous_play(audio_out))

    # asyncio.create_task(render_loop())
    asyncio.get_event_loop().run_forever()


asyncio.run(main())
