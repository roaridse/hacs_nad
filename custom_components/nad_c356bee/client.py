"""Small asynchronous NAD ASCII protocol client."""

import asyncio
from contextlib import suppress
import re

from .const import BOOL_FIELDS, QUERY_FIELDS, SOURCES


class NadClient:
    """Serialize requests and only report state confirmed by the amplifier."""

    def __init__(self, port, opener=None):
        self.port = port
        self._opener = opener
        self._reader = self._writer = None
        self._lock = asyncio.Lock()
        self._buffer = bytearray()
        self.state = {}

    async def connect(self):
        if self._writer is not None:
            return
        opener = self._opener
        if opener is None:
            from serialx import open_serial_connection

            opener = open_serial_connection
        self._reader, self._writer = await asyncio.wait_for(
            opener(url=self.port, baudrate=115200), 10
        )
        self._buffer.clear()

    async def close(self):
        writer, self._writer = self._writer, None
        self._reader = None
        self._buffer.clear()
        self.state.clear()
        if writer is not None:
            writer.close()
            with suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), 5)

    def _parse(self, line):
        match = re.fullmatch(r"Main\.([A-Za-z0-9]+)=(.+)", line)
        if not match:
            return None
        field, value = match.groups()
        if field in BOOL_FIELDS:
            if value not in ("On", "Off"):
                return None
            value = value == "On"
        elif field == "Source":
            if value not in SOURCES:
                return None
        elif field != "Model":
            return None
        self.state[field] = value
        return field

    async def _line(self):
        while True:
            for index, byte in enumerate(self._buffer):
                if byte in (10, 13):
                    line = bytes(self._buffer[:index])
                    del self._buffer[:index + 1]
                    return line.decode("ascii", errors="replace").strip()
            data = await self._reader.read(256)
            if not data:
                raise ConnectionError("Serial connection closed")
            self._buffer.extend(data)
            if len(self._buffer) > 4096:
                raise ConnectionError("Invalid serial response")

    async def _write(self, command):
        self._writer.write(f"\rMain.{command}\r".encode("ascii"))
        await self._writer.drain()

    async def _query(self, field):
        await self._write(f"{field}?")
        async with asyncio.timeout(3):
            while self._parse(await self._line()) != field:
                pass

    async def refresh(self):
        async with self._lock:
            try:
                await self.connect()
                for field in QUERY_FIELDS:
                    await self._query(field)
                model = re.sub(r"[^A-Z0-9]", "", self.state["Model"].upper())
                if model not in ("C356", "C356BEE"):
                    raise ValueError("Connected amplifier is not a C 356BEE")
                return dict(self.state)
            except (OSError, TimeoutError, ValueError):
                await self.close()
                raise

    async def command(self, field, value):
        if field in BOOL_FIELDS and value in ("On", "Off"):
            command = f"{field}={value}"
        elif field == "Source" and value in SOURCES:
            command = f"Source={value}"
        elif field == "Volume" and value in ("+", "-"):
            command = f"Volume{value}"
        else:
            raise ValueError("Unsupported command")
        async with self._lock:
            try:
                await self.connect()
                await self._write(command)
                if field != "Volume":
                    await self._query(field)
            except (OSError, TimeoutError, ValueError):
                await self.close()
                raise
