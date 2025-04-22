"""Adds config flow for Eldes."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_SCAN_INTERVAL

from .core.eldes_cloud import EldesCloud
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_EVENTS_LIST_SIZE, CONF_EVENTS_LIST_SIZE, CONF_DEVICE_IMEI

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str
    }
)


class EldesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eldes."""

    VERSION = 1

    def __init__(self):
        self.client = None
        self.devices = []
        self.data = {}

    async def async_step_user(self, user_input=None):
        """Step 1: collect email and password."""
        errors = {}

        if user_input is not None:
            email = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                session = async_get_clientsession(self.hass)
                self.client = EldesCloud(session, email, password)
                await self.client.login()

                self.devices = await self.client.get_devices()
                if not self.devices:
                    errors["base"] = "no_devices"
                else:
                    self.data[CONF_USERNAME] = email
                    self.data[CONF_PASSWORD] = password
                    return await self.async_step_select_device()

            except Exception as ex:
                _LOGGER.error("Eldes login failed: %s", ex)
                errors["base"] = "auth_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors
        )

    async def async_step_select_device(self, user_input=None):
        """Step 2: let user select device."""
        errors = {}

        device_options = {
            device["imei"]: f"{device['name']} ({device['imei']})"
            for device in self.devices
        }

        if user_input is not None:
            selected_imei = user_input["device"]
            selected_device = next((d for d in self.devices if d["imei"] == selected_imei), None)

            if selected_device:
                await self.async_set_unique_id(selected_imei)
                self._abort_if_unique_id_configured()

                self.data[CONF_DEVICE_IMEI] = selected_imei

                return self.async_create_entry(
                    title=selected_device["name"],
                    data=self.data
                )
            else:
                errors["base"] = "device_not_found"

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                vol.Required("device"): vol.In(device_options)
            }),
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for Eldes."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ): int,
                    vol.Required(
                        CONF_EVENTS_LIST_SIZE,
                        default=self.config_entry.options.get(CONF_EVENTS_LIST_SIZE, DEFAULT_EVENTS_LIST_SIZE)
                    ): int,
                }
            )
        )
