import time
import struct
from machine import Pin
import asyncio

import pypn5180
import ndef


class NfcException(Exception):
    pass


class NfcTagLost(NfcException):
    pass


class NfcTagNotFormatted(NfcException):
    pass


class NfcTag:
    def __init__(self, uid, block_size, num_blocks):
        self.uid = uid
        self.block_size = block_size
        self.num_blocks = num_blocks

        self.header_size = 0
        self.mem_size = 0

    def __repr__(self):
        return f"UID: {self.uid}  Block size: {self.block_size}  Num blocks: {self.num_blocks}  Mem size: {self.mem_size}  Header size: {self.header_size}"


class NfcTlv:
    TypeNdef = 3
    TypeProprietary = 0xFD
    TypeTerminator = 0xFE

    def __init__(self, data):
        self.type = data[0]
        self.length = data[1]
        self.size = 2
        if self.length == 0xFF:
            self.length = struct.unpack_from("<H", data[2])
            self.size = 4


def chunks(buffer, block_size):
    # This function yields chunks of the buffer of size block_size.
    for i in range(0, len(buffer), block_size):
        yield buffer[i : i + block_size]


class NfcReader:
    def __init__(self, spi, cs, busy, rst):
        self.rst = Pin(rst, Pin.OUT)
        self.reader = pypn5180.Reader(spi=spi, cs=cs, busy=busy)
        self.tag = None
        self.event_found = asyncio.Event()
        self.event_lost = asyncio.Event()
        self.lock = asyncio.Lock()
        self.retries = 1

    async def start(self, verbose=False):
        await self.reset()
        fw_version = await self.reader.pn5180.getFirmwareVersion()
        if 0 == fw_version:
            raise Exception("Failed to communicate with PN5180")
        await self.reader.start(verbose=verbose, highspeed=False)

    async def reset(self):
        self.rst.value(0)
        await asyncio.sleep(0.1)
        self.rst.value(1)

    async def read(self, offset, bytes):
        if self.tag is None:
            raise NfcTagLost()

        skip = offset % self.tag.block_size
        offset -= skip
        start_block = offset // self.tag.block_size
        total_bytes = bytes + skip
        total_bytes += self.tag.block_size - 1
        num_blocks = total_bytes // self.tag.block_size
        num_blocks -= 1

        data = []
        try:
            await self.lock.acquire()
            data, err = await self.reader.readMultipleBlocksCmd(
                start_block, num_blocks, self.tag.uid
            )
        finally:
            self.lock.release()

        return data[skip : skip + bytes]

    async def write(self, offset, data):
        if self.tag is None:
            raise NfcTagLost()

        # make sure our data is aligned to block size
        delta_pre = offset % self.tag.block_size
        data = ([0] * delta_pre) + data
        delta_post = self.tag.block_size - (len(data) % self.tag.block_size)
        data += [0] * delta_post

        # loop through block_size chunks of the data
        try:
            await self.lock.acquire()
            start_block = (offset - delta_pre) // self.tag.block_size
            for block_num, block_data in enumerate(
                chunks(data, self.tag.block_size), start=start_block
            ):
                data, err = await self.reader.writeSingleBlockCmd(
                    block_num, block_data, self.tag.uid
                )
                if data:
                    raise Exception(f"Error writing block {block_num}: {err}")
        finally:
            self.lock.release()

    async def format(self):
        if self.tag is None:
            raise NfcTagLost()

        mem_size = (self.tag.block_size * self.tag.num_blocks) // 8
        header = [0xE1, 0x40, mem_size, 0x1, 0, 0, 0, 0]
        await self.write(0, header[:4])

        self.tag.header_size = 4
        self.tag.mem_size = mem_size * 8
        return header

    async def _readHeader(self, format=False):
        if self.tag is None:
            raise NfcTagLost()

        if self.tag.header_size > 0:
            return

        self.tag.header_size = 0
        self.tag.mem_size = 0

        # read CC, which is either 4 or 8 bytes. Lets assume 4 for now to keep it simple
        header = await self.read(0, 8)
        if len(header) < 4 or header[0] not in [0xE1, 0xE2] or header[1] & 0xFC != 0x40:
            if format:
                header = await self.format()
            else:
                return

        header_size = 4
        mem_size = header[2]
        if mem_size == 0:
            mem_size = (header[6] << 8) | header[7]
            header_size = 8
        mem_size *= 8

        self.tag.header_size = header_size
        self.tag.mem_size = mem_size

    async def readNdef(self):
        if self.tag is None:
            raise NfcTagLost()

        ret = ndef.NdefMessage()

        await self._readHeader()

        if self.tag.header_size == 0:
            raise NfcTagNotFormatted()

        # read TLV records starting from offset and no more than mem_size
        offset = self.tag.header_size
        while offset < self.tag.mem_size:
            tlv = NfcTlv(await self.read(offset, 4))
            offset += tlv.size

            if tlv.type == NfcTlv.TypeNdef:
                ndef_bytes = await self.read(offset, tlv.length)
                try:
                    ret = ndef.NdefMessage(ndef_bytes)
                    break
                except ndef.InvalidNdef:
                    break

            if tlv.type == NfcTlv.TypeProprietary:
                offset += tlv.length
                continue

            if tlv.type == NfcTlv.TypeTerminator:
                break

        return ret

    async def writeNdef(self, ndefmsg):
        """Writes NdefMessage to tag, erasing all existing tag contents"""

        if self.tag is None:
            raise Exception("No tag")

        ndef_bytes = ndefmsg.to_buffer()

        # TODO: doesn't yet deal with messages > 255 bytes
        if len(ndef_bytes) > 255:
            raise NotImplemented("No support for long ndef messages")

        # format the tag if we need to (this is a no-op if already formatted)
        await self._readHeader(format=True)

        buffer = []
        buffer.append(NfcTlv.TypeNdef)
        buffer.append(len(ndef_bytes))
        buffer.extend(ndef_bytes)
        buffer.append(NfcTlv.TypeTerminator)

        await self.write(self.tag.header_size, buffer)

    async def enableMailbox(self, enabled=True):
        if self.tag is None:
            raise NfcTagLost()

        try:
            await self.lock.acquire()
            await self.reader.writeDynamicConfigurationCmd(
                0x0D, 1 if enabled else 0, self.tag.uid
            )
        finally:
            self.lock.release()

    async def writeMessage(self, message):
        if self.tag is None:
            raise Exception("No tag")

        try:
            await self.lock.acquire()
            await self.reader.writeMessageCmd(message, self.tag.uid)
        finally:
            self.lock.release()

    async def tick(self):
        current_uid = None
        try:
            await self.lock.acquire()
            current_uid, err = await self.reader.inventoryCmd()
        except Exception as e:
            # reader error, reset state and try again
            print("Attempting to reset NFC reader: ", e)
            await self.reader.start()
        finally:
            self.lock.release()

        last_uid = self.tag.uid if self.tag is not None else None
        if current_uid != last_uid:
            if not current_uid and self.retries > 0:
                self.retries -= 1
                return

            self.retries = 1

            # handle losing a tag
            if last_uid:
                self.tag = None
                self.event_found.clear()
                self.event_lost.set()

            # handle finding a tag
            if current_uid:
                # read tag info
                info = None
                try:
                    await self.lock.acquire()
                    info, err = await self.reader.getSystemInformationCmd(current_uid)
                except:
                    pass
                finally:
                    self.lock.release()

                if info:
                    try:
                        self.tag = NfcTag(current_uid, info.block_size, info.num_blocks)
                        # commented this out so the tag found callback gets called faster
                        # await self._readHeader()
                        self.event_lost.clear()
                        self.event_found.set()
                    except:
                        # error reading tag, reset state and try again
                        self.tag = None
                        self.event_found.clear()
                        self.event_lost.set()

    def onTagFound(self, callback):
        # create a task to launch a callback task and cancel it when tag is lost
        async def tag_event_handler():
            task = None
            try:
                while True:
                    await self.event_found.wait()
                    task = asyncio.create_task(callback(self))
                    await self.event_lost.wait()
                    task.cancel()
                    task = None
            except asyncio.CancelledError:
                if task:
                    task.cancel

        return asyncio.create_task(tag_event_handler())

    async def loop(self):
        while True:
            await self.tick()
            await asyncio.sleep(0.1)
