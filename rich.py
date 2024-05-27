from machine import SPI, I2C, Pin
import fern
import codec
import nfc
import asyncio
import espnow
import time
import network
import mixer

# pixelblaze GPIO
PixelBlazePin1 = Pin(fern.D1)
PixelBlazePin2 = Pin(fern.D2)
PixelBlazePin3 = Pin(fern.D3)

# keep track of tags from all controllers. dictionary keyed by controller id, value is tag id & timestamp
tags = {}

# our ESPNow broadcaster. We broadcast scanned tags to all listening controllers
broadcaster = espnow.ESPNow()
bcast = b"\xFF" * 6

TAG_SCANNED_WINDOW = 3000  # 3 seconds


# gets called when a tag is scanned locally, or remotely via ESPNow
def tag_scanned(controller_id, tag_id):
    tags[controller_id] = (tag_id, time.ticks_ms())
    print("[{0}] Tag found {1}".format(controller_id, tag_id))

    # loop through the tags and determine if we have a match
    count = 0
    for controller, tag in tags.items():
        # not scanned recently? skip
        if time.ticks_diff(time.ticks_ms(), tag[1]) > TAG_SCANNED_WINDOW:
            return
        else:
            count += 1

    if count == 3:
        print("Three tags scanned within the scan window, HOORAY")
        # do something here. look up the IDs in a table? play a sound? signal to pixelblaze? etc.
        # coolsound.play()
        # PixelBlazePin1.value(0)
        # PixelBlazePin2.value(1)
        # PixelBlazePin3.value(0)


# local tag found
async def tag_found(reader):
    try:
        mac = network.WLAN(network.STA_IF).config("mac").hex()
        tag_scanned(mac, reader.tag.uid.hex())
        broadcaster.send(bcast, reader.tag.uid)

        while True:
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        print("Tag lost")


# remote tag found
async def receiver_loop():
    while True:
        try:
            sender, tag_id = broadcaster.recv(0)
            if sender is not None and tag_id is not None:
                tag_scanned(sender.hex(), tag_id.hex())
        except Exception as e:
            print("Error receiving tag: ", e)
        await asyncio.sleep(0.2)


async def main():
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

    # print("Opening Audio Codec")
    # i2c = I2C(0, scl=fern.I2C_SCL, sda=fern.I2C_SDA)
    # codec.init(i2c)

    # print("Mounting SD card")
    # try:
    #     fern.mount_sdcard()
    # except Exception as e:
    #     print("No SD card found: ", e)

    print("Opening ESPNow")
    network.WLAN(network.STA_IF).active(True)
    broadcaster.active(True)
    broadcaster.add_peer(bcast)
    asyncio.create_task(receiver_loop())

    asyncio.get_event_loop().run_forever()


asyncio.run(main())
