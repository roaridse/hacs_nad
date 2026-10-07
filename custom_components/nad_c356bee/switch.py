"""Speaker and tape monitor switches."""

from homeassistant.components.switch import SwitchEntity

from .entity import NadEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        NadSwitch(entry.runtime_data, entry, key)
        for key in ("SpeakerA", "SpeakerB", "Tape1")
    ])


class NadSwitch(NadEntity, SwitchEntity):
    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator, entry, key)
        self.key = key
        self._attr_translation_key = key.lower()

    @property
    def is_on(self):
        return self.coordinator.data.get(self.key)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.command(self.key, "On")

    async def async_turn_off(self, **kwargs):
        await self.coordinator.command(self.key, "Off")
