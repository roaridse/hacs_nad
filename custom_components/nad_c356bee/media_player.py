"""Amplifier media player without unsupported absolute volume control."""

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass, MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState,
)

from .const import SOURCES
from .entity import NadEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([NadMediaPlayer(entry.runtime_data, entry, "amplifier")])


class NadMediaPlayer(NadEntity, MediaPlayerEntity):
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = list(SOURCES)

    @property
    def state(self):
        power = self.coordinator.data.get("Power")
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def is_volume_muted(self):
        return self.coordinator.data.get("Mute")

    @property
    def source(self):
        return self.coordinator.data.get("Source")

    async def async_turn_on(self):
        await self.coordinator.command("Power", "On")

    async def async_turn_off(self):
        await self.coordinator.command("Power", "Off")

    async def async_mute_volume(self, mute):
        await self.coordinator.command("Mute", "On" if mute else "Off")

    async def async_select_source(self, source):
        await self.coordinator.command("Source", source)

    async def async_volume_up(self):
        await self.coordinator.command("Volume", "+")

    async def async_volume_down(self):
        await self.coordinator.command("Volume", "-")
