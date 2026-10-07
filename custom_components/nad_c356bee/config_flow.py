"""Select a local or ESPHome-proxied serial port."""

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_DEVICE
from homeassistant.helpers.selector import SerialPortSelector

from .client import NadClient
from .const import DOMAIN


class NadConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one amplifier per serial port."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_DEVICE: user_input[CONF_DEVICE]})
            client = NadClient(user_input[CONF_DEVICE])
            try:
                await client.refresh()
            except ValueError:
                errors["base"] = "invalid_device"
            except (OSError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="NAD C 356BEE", data=user_input)
            finally:
                await client.close()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): SerialPortSelector()}),
            errors=errors,
        )
