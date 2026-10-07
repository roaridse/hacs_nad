"""Protocol tests without requiring a running Home Assistant installation."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "nad_protocol_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "custom_components/nad_c356bee")]
sys.modules[PACKAGE] = package
spec = importlib.util.spec_from_file_location(
    f"{PACKAGE}.client", ROOT / "custom_components/nad_c356bee/client.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NadClient = module.NadClient


class FakeWriter:
    def __init__(self, reader):
        self.reader = reader
        self.commands = []
        self.closed = False
        self.values = {
            "Model": "C356BEE", "Power": "Off", "Mute": "Off",
            "SpeakerA": "On", "SpeakerB": "Off", "Tape1": "Off", "Source": "CD",
        }

    def write(self, data):
        self.commands.append(data)
        text = data.decode().strip()[5:]
        if text.endswith("?"):
            field = text[:-1]
            # Include echoes, malformed lines and mixed delimiters.
            reply = f"\rMain.{field}?\r\nnoise\nMain.{field}={self.values[field]}\r\n"
            for byte in reply.encode():
                self.reader.feed_data(bytes([byte]))
        elif "=" in text:
            field, value = text.split("=")
            self.values[field] = value

    async def drain(self):
        pass

    def close(self):
        self.closed = True

    async def wait_closed(self):
        pass


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.reader = asyncio.StreamReader()
        self.writer = FakeWriter(self.reader)

        async def opener(**kwargs):
            self.assertEqual(kwargs, {"url": "esphome-hass://proxy/port", "baudrate": 115200})
            return self.reader, self.writer

        self.client = NadClient("esphome-hass://proxy/port", opener)

    async def asyncTearDown(self):
        await self.client.close()

    async def test_refresh_and_commands(self):
        state = await self.client.refresh()
        self.assertFalse(state["Power"])
        self.assertTrue(state["SpeakerA"])
        self.assertEqual(state["Source"], "CD")
        self.assertEqual(len(self.writer.commands), 7)
        self.assertTrue(all(cmd.startswith(b"\rMain.") and cmd.endswith(b"\r") for cmd in self.writer.commands))
        await self.client.command("Power", "On")
        self.assertTrue(self.client.state["Power"])
        await self.client.command("Source", "Aux")
        self.assertEqual(self.client.state["Source"], "Aux")
        await self.client.command("Volume", "+")
        self.assertEqual(self.writer.commands[-1], b"\rMain.Volume+\r")
        await self.client.command("Volume", "-")
        self.assertEqual(self.writer.commands[-1], b"\rMain.Volume-\r")
        self.assertNotIn("Volume", self.client.state)

    async def test_wrong_model_closes_connection(self):
        self.writer.values["Model"] = "C368"
        with self.assertRaises(ValueError):
            await self.client.refresh()
        self.assertTrue(self.writer.closed)
        self.assertEqual(self.client.state, {})

    async def test_eof_closes_connection(self):
        await self.client.connect()
        self.reader.feed_eof()
        self.writer.write = lambda data: None
        with self.assertRaises(ConnectionError):
            await self.client.refresh()
        self.assertTrue(self.writer.closed)

    async def test_invalid_commands_never_sent(self):
        for field, value in (("Volume", "50"), ("Source", "CD\rMain.Power=On"), ("Power", "yes")):
            with self.assertRaises(ValueError):
                await self.client.command(field, value)
        self.assertEqual(self.writer.commands, [])

    async def test_parser_rejects_invalid_values(self):
        for line in ("Main.Power=Maybe", "Main.Source=Unknown", "Main.Volume=20", "junk"):
            self.assertIsNone(self.client._parse(line))
        self.assertEqual(self.client.state, {})

    async def test_fragmented_frames(self):
        await self.client.connect()

        async def feed():
            for part in (b"Main.Po", b"wer=On", b"\r\nMain.Mute=Off\n"):
                await asyncio.sleep(0)
                self.reader.feed_data(part)

        feeder = asyncio.create_task(feed())
        self.assertEqual(await self.client._line(), "Main.Power=On")
        self.assertEqual(await self.client._line(), "")
        self.assertEqual(await self.client._line(), "Main.Mute=Off")
        await feeder

    async def test_concurrent_requests_are_serialized(self):
        await self.client.refresh()
        await asyncio.gather(
            self.client.command("Mute", "On"), self.client.command("SpeakerB", "On")
        )
        self.assertEqual(self.writer.commands[-4:], [
            b"\rMain.Mute=On\r", b"\rMain.Mute?\r",
            b"\rMain.SpeakerB=On\r", b"\rMain.SpeakerB?\r",
        ])


if __name__ == "__main__":
    unittest.main()
