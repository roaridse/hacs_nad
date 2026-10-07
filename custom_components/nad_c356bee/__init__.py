"""NAD C 356BEE integration."""

from datetime import timedelta

from homeassistant.const import CONF_DEVICE, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

from .client import NadClient

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SWITCH]


class NadCoordinator(DataUpdateCoordinator):
    """Poll the amplifier and reconnect after transport failures."""

    def __init__(self, hass, client):
        super().__init__(
            hass, logging.getLogger(__name__), name="NAD C 356BEE",
            update_interval=timedelta(seconds=15),
        )
        self.client = client

    async def _async_update_data(self):
        try:
            return await self.client.refresh()
        except (OSError, TimeoutError, ValueError) as err:
            raise UpdateFailed("Cannot read amplifier state") from err

    async def command(self, field, value):
        try:
            await self.client.command(field, value)
        except (OSError, TimeoutError, ValueError) as err:
            self.async_set_update_error(UpdateFailed("Cannot send amplifier command"))
            raise HomeAssistantError("Cannot send amplifier command") from err
        self.async_set_updated_data(dict(self.client.state))


async def async_setup_entry(hass, entry):
    client = NadClient(entry.data[CONF_DEVICE])
    coordinator = NadCoordinator(hass, client)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await client.close()
        raise
    async def close_on_stop(event):
        await client.close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_on_stop)
    )
    return True


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.client.close()
        return True
    return False
